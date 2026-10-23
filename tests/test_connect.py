"""Connect must not expose the workspace or execute against server projects."""
import os
import subprocess
import sys


def test_connect_entrypoint_isolated(tmp_path):
    script = r'''
import asyncio, json, sys
from fastapi.testclient import TestClient
from gitide_server import connect, connect_auth as auth
from gitide_server.database import SessionLocal, Project, User
from gitide_server.mcp_server import request_grant
from types import SimpleNamespace
for module in ("main", "agent", "vcs", "git_bridge", "mcp_terminal"):
    assert "gitide_server." + module not in sys.modules
with SessionLocal() as db:
    user = db.query(User).filter_by(role="root").first()
    cookie = auth.sign_session(user.id)
    local = Project(name="Local", path="", storage_kind="device", device_id="a"*32, root_id="b"*32)
    legacy = Project(name="Legacy", path=str(__import__("pathlib").Path.cwd()), storage_kind="server")
    db.add_all([local, legacy]); db.commit()
    local_id, legacy_id = local.id, legacy.id
with TestClient(connect.app) as client:
    assert client.get("/", follow_redirects=False).headers["location"] == "/connect-device"
    assert client.get("/connect-device", follow_redirects=False).status_code == 303
    assert client.get("/login").status_code == 200
    for path in ("/static/index.html", "/static/app.js", "/diagrams", "/api/projects", "/api/config", "/docs"):
        assert client.get(path).status_code == 404, path
    client.cookies.set("gitide_session", cookie)
    for path in ("/connect-device", "/local-devices"):
        page = client.get(path)
        assert page.status_code == 200 and "Okestre Connect" in page.text
        assert "<style>" in page.text and "color-scheme:dark" in page.text
        assert "/* Setup only." in page.text
        assert '<script src="/static/' not in page.text
        assert '<link rel="stylesheet"' not in page.text
    for asset in ("local-devices.css", "local-devices.js"):
        assert client.get("/static/" + asset).status_code == 200
    assert client.post("/api/projects/1/commands/execute", json={"command":"whoami"}).status_code == 404
    state = client.get("/api/local/devices").json()
    pair = client.post("/api/local/pair", json={"name":"test"}, headers={"X-CSRF-Token":state["csrf_token"]})
    assert pair.status_code == 200, pair.text
    assert client.get("/.well-known/oauth-authorization-server").status_code == 200
    assert client.post("/mcp/", json={}).status_code == 401
    assert client.get("/api/local/status").status_code == 401
    assert client.post("/api/local/claim", json={"code":pair.json()["code"]}).status_code == 200
    assert client.get("/api/mcp/connections").status_code == 200
    assert connect.consent_projects() == [{"id":local_id,"name":"Local"}]
    async def tools():
        token = request_grant.set(SimpleNamespace(subject=str(user.id), project_ids=None, can_write=True, can_execute=True))
        try:
            projects = await connect.mcp_server.call_tool("list_projects", {})
            assert "Legacy" not in str(projects) and "Local" in str(projects)
            try:
                await connect.mcp_server.call_tool("read_file", {"project_id":legacy_id,"filepath":"requirements.txt"})
            except Exception as exc:
                assert "connect_requires_device_project" in str(exc), exc
            else:
                raise AssertionError("Connect exposed a server project")
        finally:
            request_grant.reset(token)
    asyncio.run(tools())
print("connect isolated OK")
'''
    env = dict(os.environ, GITIDE_DATA_DIR=str(tmp_path / "data"), GITIDE_ROOT_EMAIL="test@example.invalid")
    result = subprocess.run([sys.executable, "-c", script], env=env, text=True, capture_output=True, timeout=40)
    assert result.returncode == 0, result.stderr + result.stdout
    assert "connect isolated OK" in result.stdout
