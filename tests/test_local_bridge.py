import asyncio
import json
import socket
import sqlite3
import threading
import time
import uuid
from types import SimpleNamespace

import httpx
import pytest
import uvicorn
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from starlette.staticfiles import StaticFiles
from pathlib import Path

from gitide_server.database import Base, Project, FileSnapshot, migrate_project_storage
from gitide_server.local_bridge import DeviceStore, LocalBridge
from gitide_server.mcp_server import create_mcp
from okestre_local.client import Agent
from okestre_local.config import Config
from okestre_local.protocol import BridgeError


def eventually(predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.05)
    raise AssertionError("condition did not become true")


@pytest.fixture
def live(tmp_path, request):
    engine = create_engine("sqlite:///" + str(tmp_path / "server.db"))
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    state = SimpleNamespace(grant=SimpleNamespace(subject="1", project_ids=None, can_write=True), active=True)
    oauth = SimpleNamespace(
        active_subject=lambda subject: state.active and subject in ("1", "2"),
        current_user=lambda request: SimpleNamespace(id=1, role="root") if request.cookies.get("session") == "owner" else None,
        management_csrf=lambda request, user: "test-csrf",
    )
    bridge = LocalBridge(DeviceStore(tmp_path / "devices.db"), sessions, oauth)
    _, transport, lifespan = create_mcp(lambda request: state.grant if request.headers.get("authorization") == "Bearer test" else False,
                                       sessions, bridge=bridge, remote_only=getattr(request, "param", False))
    app = FastAPI(lifespan=lifespan)
    app.router.routes.extend(bridge.routes())
    app.mount("/mcp", transport)
    app.mount("/static", StaticFiles(directory=Path(__file__).parents[1] / "gitide_server/static"))
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="critical", ws_max_size=8 * 1024 * 1024))
    thread = threading.Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
    thread.start()
    eventually(lambda: server.started)
    url = f"http://127.0.0.1:{port}"
    client = httpx.Client(base_url=url, cookies={"session": "owner"}, headers={"X-CSRF-Token": "test-csrf"}, timeout=10)
    state.bridge, state.client, state.url, state.sessions = bridge, client, url, sessions
    state.agents = []
    def enroll():
        code = client.post("/api/local/pair", json={"name": "Windows de teste"}).json()["code"]
        config = Config(tmp_path / ("local-" + uuid.uuid4().hex))
        config.pair(url, code)
        folder = tmp_path / ("project-" + uuid.uuid4().hex)
        folder.mkdir()
        marker = "ONLY_ON_COMPUTER_" + uuid.uuid4().hex
        (folder / "README.md").write_text(marker, encoding="utf-8")
        root_id = config.add_root(folder, "Projeto local", True)
        agent = Agent(config)
        agent_thread = threading.Thread(target=lambda: asyncio.run(agent.run()), daemon=True)
        state.agents.append((agent, agent_thread))
        agent_thread.start()
        identifier = config.load()["device_id"]
        eventually(lambda: bridge.online(identifier))
        result = client.post("/api/local/bind", json={"device_id": identifier, "root_id": root_id, "name": "Local " + root_id[:8]})
        assert result.status_code == 200, result.text
        return config, folder, marker, result.json()["project_id"]
    state.enroll = enroll
    def tool(name, **arguments):
        response = client.post("/mcp/", headers={"Authorization": "Bearer test", "Accept": "application/json, text/event-stream"},
                               json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
        assert response.status_code == 200, response.text
        return response.json()["result"]
    state.tool = tool
    yield state
    for agent, agent_thread in state.agents:
        agent.stopping.set()
        agent_thread.join(7)
        assert not agent_thread.is_alive()
    client.close()
    server.should_exit = True
    thread.join(8)
    assert not thread.is_alive()
    sock.close()
    engine.dispose()


@pytest.mark.parametrize("live", [False, True], indirect=True)
def test_end_to_end_mcp_reads_edits_and_keeps_server_content_free(live, tmp_path):
    config, folder, marker, project = live.enroll()
    read = live.tool("read_file", project_id=project, filepath="README.md")
    assert not read.get("isError"), read
    assert read["structuredContent"]["content"] == marker
    result = live.tool("write_file", project_id=project, filepath="README.md", content=marker + " changed", expected_sha256=read["structuredContent"]["sha256"])
    assert not result.get("isError"), result
    assert folder.joinpath("README.md").read_text() == marker + " changed"
    assert live.tool("search_files", project_id=project, query="changed")["structuredContent"]["items"][0]["filepath"] == "README.md"
    with live.sessions() as db:
        assert db.query(FileSnapshot).count() == 0
        with pytest.raises(ValueError, match="requires_local_bridge"):
            _ = db.get(Project, project).path
    for name in ("server.db", "devices.db"):
        assert marker.encode() not in (tmp_path / name).read_bytes()
    data = live.client.get("/api/local/devices").json()
    assert str(folder) not in json.dumps(data)
    assert config.load()["token"] not in json.dumps(data)
    assert live.tool("execute_command", project_id=project, command="echo forbidden")["isError"]
    assert live.tool("git_status", project_id=project)["isError"]


def test_oauth_owner_write_grant_and_offline(live):
    config, folder, marker, project = live.enroll()
    live.grant.can_write = False
    assert live.tool("write_file", project_id=project, filepath="README.md", content="no", expected_sha256="missing")["isError"]
    live.grant.subject = "2"
    assert live.tool("read_file", project_id=project, filepath="README.md")["isError"]
    live.grant = True
    assert live.tool("read_file", project_id=project, filepath="README.md")["isError"]
    live.grant = SimpleNamespace(subject="1", project_ids=[], can_write=True)
    assert live.tool("read_file", project_id=project, filepath="README.md")["isError"]
    live.grant.project_ids = [project]
    agent, thread = live.agents[0]
    agent.stopping.set()
    thread.join(7)
    eventually(lambda: not live.bridge.online(config.load()["device_id"]))
    assert "device_offline" in str(live.tool("read_file", project_id=project, filepath="README.md"))
    assert folder.joinpath("README.md").read_text() == marker


def test_pairing_csrf_revocation_and_local_pause(live):
    client = live.client
    assert httpx.get(live.url + "/api/local/devices").status_code == 403
    assert client.post("/api/local/pair", json={"name": "no"}, headers={"X-CSRF-Token": "bad"}).status_code == 403
    code = client.post("/api/local/pair", json={"name": "one use"}).json()["code"]
    assert client.post("/api/local/claim", json={"code": code}).status_code == 200
    assert client.post("/api/local/claim", json={"code": code}).status_code == 400
    config, _, _, project = live.enroll()
    settings = config.load()
    settings["paused"] = True
    config.save(settings)
    eventually(lambda: not live.bridge.online(settings["device_id"]))
    settings["paused"] = False
    config.save(settings)
    eventually(lambda: live.bridge.online(settings["device_id"]), seconds=10)
    assert not live.tool("read_file", project_id=project, filepath="README.md").get("isError")
    assert client.post("/api/local/revoke", json={"device_id": settings["device_id"]}).status_code == 200
    assert "device_not_authorized" in str(live.tool("read_file", project_id=project, filepath="README.md"))
    assert live.bridge.store.authenticate(settings["token"]) is None


def test_additive_migration(tmp_path):
    engine = create_engine("sqlite:///" + str(tmp_path / "old.db"))
    with engine.begin() as db:
        db.execute(text("CREATE TABLE projects (id INTEGER PRIMARY KEY,name TEXT,path TEXT,git_remote TEXT,created_at DATETIME)"))
        db.execute(text("INSERT INTO projects(id,name,path) VALUES (1,'old','old-path')"))
    migrate_project_storage(engine)
    migrate_project_storage(engine)
    with engine.connect() as db:
        assert db.execute(text("SELECT storage_kind,path,device_id FROM projects")).fetchone() == ("server", "old-path", None)
    engine.dispose()


def test_batch_binding_is_atomic_authorized_and_repeatable(live):
    config, _, _, existing = live.enroll()
    device = config.load()['device_id']
    a, b = uuid.uuid4().hex, uuid.uuid4().hex
    live.bridge.store.roots(device, [{'id': a, 'name': 'Alpha', 'writable': True}, {'id': b, 'name': 'Beta', 'writable': False}])
    with live.sessions() as db:
        existing_name = db.get(Project, existing).name
    url = '/api/local/bind-many'
    payload = {'device_id': device, 'projects': [{'root_id': a, 'name': 'Alpha'}, {'root_id': b, 'name': existing_name}]}
    result = live.client.post(url, json=payload)
    assert result.status_code == 400 and result.json()['detail'] == 'project_name_exists'
    with live.sessions() as db:
        assert db.query(Project).filter_by(root_id=a).count() == 0
    payload['projects'][1]['name'] = 'Beta'
    assert live.client.post(url, json=payload, headers={'X-CSRF-Token': 'bad'}).status_code == 403
    wrong = dict(payload, device_id='f' * 32)
    assert live.client.post(url, json=wrong).status_code == 400
    result = live.client.post(url, json=payload)
    assert result.status_code == 200, result.text
    assert len(result.json()['projects']) == 2
    assert live.client.post(url, json=payload).json() == result.json()
    with live.sessions() as db:
        assert db.query(Project).count() == 3
    payload['projects'][1]['root_id'] = a
    assert live.client.post(url, json=payload).status_code == 400


def test_slow_request_and_inactive_owner(live):
    config, folder, marker, project = live.enroll()
    agent, _ = live.agents[0]
    original = agent.executor.dispatch
    def slow(message):
        time.sleep(31)
        return original(message)
    agent.executor.dispatch = slow
    live.client.timeout = httpx.Timeout(45)
    assert live.tool("read_file", project_id=project, filepath="README.md")["structuredContent"]["content"] == marker
    agent.executor.dispatch = original
    live.active = False
    assert "device_not_authorized" in str(live.tool("read_file", project_id=project, filepath="README.md"))
    assert folder.joinpath("README.md").read_text() == marker


def test_packaged_windows_agent_with_real_mcp(live):
    import os
    import subprocess
    executable = Path(os.environ.get("OKESTRE_TEST_EXECUTABLE", str(Path(__file__).parents[1] / "outputs/okestre-local/OkestreLocal/OkestreLocal.exe")))
    if os.name != "nt" or not executable.exists():
        pytest.skip("Build the Windows portable executable to run this test")
    config, folder, marker, project = live.enroll()
    agent, thread = live.agents[0]
    agent.stopping.set()
    thread.join(7)
    eventually(lambda: not live.bridge.online(config.load()["device_id"]))
    process = subprocess.Popen([str(executable), "--home", str(config.home), "run"], creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        eventually(lambda: live.bridge.online(config.load()["device_id"]), seconds=10)
        read = live.tool("read_file", project_id=project, filepath="README.md")["structuredContent"]
        assert read["content"] == marker
        result = live.tool("write_file", project_id=project, filepath="README.md", content="packaged executable edit", expected_sha256=read["sha256"])
        assert not result.get("isError"), result
        assert folder.joinpath("README.md").read_text() == "packaged executable edit"
        live.grant.can_execute = True
        terminal = live.tool("execute_command", project_id=project, command="echo packaged-terminal")
        assert not terminal.get("isError"), terminal
        assert "packaged-terminal" in terminal["structuredContent"]["output"]
        subprocess.run(["git", "init", str(folder)], capture_output=True, check=True)
        assert "README.md" in live.tool("git_status", project_id=project)["structuredContent"]["output"]
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_multiple_pending_computers_expiry_and_one_use_codes(live):
    client = live.client
    pairs = []
    for number, duration in enumerate((1, 3, 9, None), 1):
        result = client.post("/api/local/pair",
                             json={"name": f"Computador {number}", "expires_in_months": duration})
        assert result.status_code == 200, result.text
        assert result.json()["expires_in"] is None
        pairs.append(result.json()["code"])
    assert len(set(pairs)) == 4
    listing = client.get("/api/local/devices").json()
    assert sum(d["pending"] for d in listing["devices"]) == 4
    assert not any(code in json.dumps(listing) for code in pairs)
    assert client.post("/api/local/pair", json={"name": "invalido", "expires_in_months": 2}).status_code == 400
    assert client.post("/api/local/pair", json={"name": "invalido", "expires_in_months": True}).status_code == 400
    for duration, code in zip((1, 3, 9, None), pairs):
        claim = client.post("/api/local/claim", json={"code": code})
        assert claim.status_code == 200, claim.text
        assert client.post("/api/local/claim", json={"code": code}).status_code == 400
        device_id, token = claim.json()["device_id"], claim.json()["token"]
        stored = live.bridge.store.get(device_id)
        assert stored is not None
        assert stored["token_hash"] != token
        assert live.bridge.store.authenticate(token)["id"] == device_id
        if duration is None:
            assert stored["expires_at"] is None
        else:
            assert stored["created"] < stored["expires_at"]
            assert stored["expires_at"] == pytest.approx(
                live.bridge.store.months_after(stored["created"], duration))
    assert not any(d["pending"] for d in client.get("/api/local/devices").json()["devices"])


def test_expired_token_does_not_authenticate_or_show_online(live):
    config, folder, marker, project = live.enroll()
    identifier, token = config.load()["device_id"], config.load()["token"]
    with live.bridge.store.connect() as db:
        db.execute("UPDATE devices SET expires_at=? WHERE id=?", (time.time() - 1, identifier))
    assert live.bridge.store.authenticate(token) is None
    assert live.bridge.store.get(identifier) is None
    state = live.client.get("/api/local/devices").json()["devices"]
    expired = next(item for item in state if item["id"] == identifier)
    assert expired["expired"]
    assert not expired["online"]
    assert not any(p["id"] == project for p in live.client.get("/api/local/devices").json()["projects"])
    assert "device_not_authorized" in str(live.tool("read_file", project_id=project, filepath="README.md"))
    assert folder.joinpath("README.md").read_text() == marker


def test_remove_folder_access_preserves_physical_content_and_blocks_project(live):
    config, folder, marker, project = live.enroll()
    settings = config.load()
    device_id = settings["device_id"]
    root_id = next(iter(settings["roots"]))
    before = live.client.get("/api/local/devices").json()
    assert any(r["id"] == root_id for d in before["devices"] for r in d["roots"])
    assert live.bridge.store.remove_root(device_id, root_id, owner="2") is False
    bad = live.client.post("/api/local/remove-root",
        json={"device_id": device_id, "root_id": "not-a-root"})
    assert bad.status_code == 400
    result = live.client.post("/api/local/remove-root",
        json={"device_id": device_id, "root_id": root_id})
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "removed"
    after = live.client.get("/api/local/devices").json()
    assert not any(r["id"] == root_id for d in after["devices"] for r in d["roots"])
    assert not any(p["id"] == project for p in after["projects"])
    assert live.client.post("/api/local/bind",
        json={"device_id": device_id, "root_id": root_id, "name": "Outra pasta"}).status_code == 400
    assert live.client.post("/api/local/bind-many",
        json={"device_id": device_id, "projects": [{"root_id": root_id, "name": "Outra pasta"}]}).status_code == 400
    assert "root_unavailable" in str(live.tool("read_file", project_id=project, filepath="README.md"))
    assert folder.joinpath("README.md").read_text() == marker
    # Revocation remains active in durable SQLite independently of the running channel.
    assert root_id in json.loads(live.bridge.store.get(device_id)["blocked_roots"])
    assert live.client.post("/api/local/remove-root",
        json={"device_id": device_id, "root_id": root_id}).status_code == 200


def test_expiry_uses_calendar_months_and_preserves_end_of_month():
    from datetime import datetime, timezone
    jan_31 = datetime(2027, 1, 31, 12, 45, tzinfo=timezone.utc).timestamp()
    actual = DeviceStore.months_after(jan_31, 1)
    assert datetime.fromtimestamp(actual, timezone.utc) == datetime(
        2027, 2, 28, 12, 45, tzinfo=timezone.utc)
    leap = datetime(2028, 1, 31, tzinfo=timezone.utc).timestamp()
    assert datetime.fromtimestamp(DeviceStore.months_after(leap, 1), timezone.utc) == datetime(
        2028, 2, 29, tzinfo=timezone.utc)
    assert DeviceStore.months_after(jan_31, None) is None


def test_store_additive_migration_preserves_old_device_tokens(tmp_path):
    database = tmp_path / "legacy_devices.db"
    with sqlite3.connect(database) as db:
        db.executescript("""
            CREATE TABLE devices (id TEXT PRIMARY KEY, owner TEXT NOT NULL, name TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE, roots TEXT NOT NULL DEFAULT '[]',
                created REAL NOT NULL, revoked REAL);
            CREATE TABLE pairing (code_hash TEXT PRIMARY KEY, owner TEXT NOT NULL,
                name TEXT NOT NULL, expires REAL NOT NULL);
        """)
        db.execute("INSERT INTO devices VALUES (?,?,?,?,?,?,?)",
                   ("legacy", "1", "antigo", DeviceStore.digest("legacy-secret"), "[]", time.time(), None))
    store = DeviceStore(database)
    store_again = DeviceStore(database)
    assert store_again.authenticate("legacy-secret")["expires_at"] is None
    assert store_again.page("1")[0]["name"] == "antigo"


def test_disconnect_releases_pending_request_even_if_socket_already_closed():
    from gitide_server.local_bridge import Channel
    from starlette.websockets import WebSocketDisconnect
    async def scenario():
        class ClosedSocket:
            async def close(self, **kwargs):
                raise WebSocketDisconnect(1006)
        bridge = LocalBridge(None, None, None)
        future = asyncio.get_running_loop().create_future()
        bridge.channels['device'] = Channel(ClosedSocket(), {}, {'request': future})
        await bridge.disconnect('device')
        assert 'device' not in bridge.channels
        with pytest.raises(BridgeError, match='device_disconnected_result_unknown'):
            await future
    asyncio.run(scenario())

def test_local_terminal_jobs_permissions_and_git(live):
    import subprocess
    config, folder, marker, project = live.enroll()
    command = 'echo local-terminal>terminal.txt'
    denied = live.tool('execute_command', project_id=project, command=command)
    assert denied.get('isError') and not (folder / 'terminal.txt').exists()
    live.grant.can_execute = True
    result = live.tool('execute_command', project_id=project, command=command)
    assert not result.get('isError'), result
    job = result['structuredContent']['command_id']
    eventually(lambda: (folder / 'terminal.txt').exists())
    polled = live.tool('execute_command', project_id=project, command=command, command_id=job)
    assert polled['structuredContent']['exit_code'] == 0
    assert 'local-terminal' in (folder / 'terminal.txt').read_text()
    subprocess.run(['git', 'init', str(folder)], check=True, capture_output=True)
    status = live.tool('git_status', project_id=project)
    assert not status.get('isError'), status
    assert 'terminal.txt' in status['structuredContent']['output']
    subprocess.run(['git', '-C', str(folder), 'add', 'README.md'], check=True)
    diff = live.tool('git_diff', project_id=project, filepath='README.md', staged=True)
    assert marker in diff['structuredContent']['diff']
    live.grant.can_write = False
    assert live.tool('execute_command', project_id=project, command='echo denied')['isError']


def test_pairing_code_has_no_time_expiry(tmp_path, monkeypatch):
    import gitide_server.local_bridge as module
    store = DeviceStore(tmp_path / "no-expiry.db")
    code = store.pair("1", "Persistent code")
    future = time.time() + 10 * 365 * 86400
    monkeypatch.setattr(module.time, "time", lambda: future)
    assert any(item["pending"] for item in store.page("1"))
    reopened = DeviceStore(tmp_path / "no-expiry.db")
    result = reopened.claim(code)
    assert result["device_id"]
    with pytest.raises(BridgeError):
        reopened.claim(code)


def test_new_pairing_code_replaces_previous_without_affecting_other_computer(tmp_path):
    store = DeviceStore(tmp_path / "replacement.db")
    first = store.pair("1", "Computer A")
    other = store.pair("1", "Computer B")
    replacement = store.pair("1", "Computer A")
    with pytest.raises(BridgeError):
        store.claim(first)
    assert store.claim(replacement)["device_id"]
    assert store.claim(other)["device_id"]
