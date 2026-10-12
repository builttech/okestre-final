import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

import pytest

from okestre_local.config import Config, server_url
from okestre_local.executor import Executor
from okestre_local.protocol import BridgeError


@pytest.fixture
def agent(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "hello.txt").write_bytes("primeira\nsegunda\n".encode())
    identifier = uuid.uuid4().hex
    executor = Executor({identifier: {"path": str(root), "writable": True}}, tmp_path / "state")
    def message(operation, **arguments):
        return dict(type="call", version=1, request_id=uuid.uuid4().hex, root_id=identifier,
                    operation=operation, arguments=arguments, can_write=True, deadline=time.time() + 30)
    return executor, root, message


def test_read_search_and_local_mutation_deduplication(agent):
    executor, root, message = agent
    read = executor.dispatch(message("read_file", filepath="hello.txt", limit=1))
    assert read["content"] == "primeira\n" and read["next_line"] == 2
    found = executor.dispatch(message("search_files", query="SEGUNDA"))
    assert found["items"][0]["line"] == 2
    patch = message("patch_file", filepath="hello.txt", expected_sha256=read["sha256"], target_content="primeira", replacement_content="terceira")
    result = executor.dispatch(patch)
    assert root.joinpath("hello.txt").read_text() == "terceira\nsegunda\n"
    assert executor.dispatch(patch) == result
    restarted = Executor(executor.roots, executor.data_dir)
    assert restarted.dispatch(patch) == result
    with executor.database() as db:
        assert db.execute("SELECT previous FROM snapshots").fetchone()[0] == b"primeira\nsegunda\n"
        assert db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 1
    with pytest.raises(BridgeError, match="conflict"):
        executor.dispatch(message("write_file", filepath="hello.txt", expected_sha256=read["sha256"], content="stale"))
    patch["arguments"]["replacement_content"] = "different"
    with pytest.raises(BridgeError, match="request_id_conflict"):
        executor.dispatch(patch)


@pytest.mark.parametrize("path", ["../outside.txt", "C:/outside.txt", "/outside", "\\\\server\\share", "file.txt:secret", "CON", "nul.txt", "folder./file", "folder /file", ".git/config", ".env", ".env.local", "tokens.json", ".okestre-local/state", "private.pem"])
def test_path_policy(agent, path):
    executor, _, message = agent
    with pytest.raises(BridgeError):
        executor.dispatch(message("read_file", filepath=path))


def test_permissions_legacy_deadline_unsupported_and_invalid_args(agent):
    executor, root, message = agent
    call = message("write_file", filepath="new.txt", expected_sha256="missing", content="no")
    call["can_write"] = False
    with pytest.raises(BridgeError, match="read_only"):
        executor.dispatch(call)
    call["can_write"] = True
    executor.roots[call["root_id"]]["writable"] = False
    with pytest.raises(BridgeError, match="read_only"):
        executor.dispatch(call)
    expired = message("read_file", filepath="hello.txt")
    expired["deadline"] = time.time() - 1
    assert executor.dispatch(expired)["content"] == root.joinpath("hello.txt").read_text()
    expired["deadline"] = time.time() + 86400
    assert executor.dispatch(expired)["content"]
    expired.pop("deadline")
    assert executor.dispatch(expired)["content"]
    for args in ({"filepath": "hello.txt", "limit": -1}, {"filepath": "hello.txt", "unknown": True}):
        with pytest.raises(BridgeError, match="invalid_arguments"):
            executor.dispatch(message("read_file", **args))
    with pytest.raises(BridgeError, match="unsupported_operation"):
        executor.dispatch(message("unsupported_command", command="echo no"))
    assert not (root / "new.txt").exists()


def test_ignore_hardlinks_size_and_binary(agent, tmp_path):
    executor, root, message = agent
    (root / ".gitideignore").write_text("blocked.txt\nprivate/\n")
    (root / "blocked.txt").write_text("secret")
    (root / ".env").write_text("secret")
    (root / "huge.txt").write_bytes(b"x" * (1024 * 1024 + 1))
    (root / "binary.txt").write_bytes(b"\x00")
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    os.link(outside, root / "hard.txt")
    for path in ("blocked.txt", "huge.txt", "binary.txt", "hard.txt"):
        with pytest.raises(BridgeError):
            executor.dispatch(message("read_file", filepath=path))
    items = executor.dispatch(message("list_files"))["items"]
    assert not {".env", "blocked.txt", "hard.txt"} & {i["path"] for i in items}


def test_junction_or_symlink_escape(agent, tmp_path):
    import subprocess
    executor, root, message = agent
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("never transmit")
    link = root / "shortcut"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], check=True, capture_output=True)
    else:
        link.symlink_to(outside, target_is_directory=True)
    try:
        with pytest.raises(BridgeError):
            executor.dispatch(message("read_file", filepath="shortcut/secret.txt"))
        assert all(not i["path"].startswith("shortcut/") for i in executor.dispatch(message("list_files"))["items"])
    finally:
        if os.name == "nt":
            link.rmdir()
        else:
            link.unlink()


def test_tasks_snapshots_and_pending_crash(agent):
    executor, root, message = agent
    (root / ".documents/task").mkdir(parents=True)
    result = executor.dispatch(message("create_task", code="TASK-REQ-01-001", title="Implementar", expected_sha256="missing"))
    tasks = executor.dispatch(message("list_tasks"))
    assert tasks["sha256"] == result["sha256"]
    assert tasks["items"][0]["checked"] is False
    executor.dispatch(message("update_task", code="TASK-REQ-01-001", checked=True, expected_sha256=tasks["sha256"]))
    assert executor.dispatch(message("list_tasks"))["items"][0]["checked"] is True
    call = message("write_file", filepath="new.txt", content="not repeated", expected_sha256="missing")
    fingerprint = hashlib.sha256(json.dumps([call["root_id"], call["operation"], call["arguments"]], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    with executor.database() as db:
        db.execute("INSERT INTO mutations VALUES (?,?,?,NULL,?)", (call["request_id"], fingerprint, "started", time.time()))
    with pytest.raises(BridgeError, match="mutation_indeterminate"):
        executor.dispatch(call)
    assert not (root / "new.txt").exists()


def test_protected_config_and_single_instance(tmp_path):
    config = Config(tmp_path / "state")
    config.save({"token": "private-device-credential", "roots": {}})
    assert config.load()["token"] == "private-device-credential"
    if os.name == "nt":
        assert b"private-device-credential" not in config.file.read_bytes()
    with config.single_instance():
        with pytest.raises(OSError):
            with Config(config.home).single_instance():
                pass
    for url in ("http://remote.example", "https://user:password@example.org", "https://example.org/mcp", "https://example.org?secret=1"):
        with pytest.raises(BridgeError):
            server_url(url)
    assert server_url("http://127.0.0.1:8000/") == "http://127.0.0.1:8000"

def test_terminal_long_job_poll_stop_and_root_isolation(agent):
    import subprocess
    import sys
    executor, root, message = agent
    command = subprocess.list2cmdline([sys.executable, '-u', '-c', 'import time; print("ready", flush=True); time.sleep(90)']) if os.name == 'nt' else "python3 -u -c 'import time; print(\"ready\", flush=True); time.sleep(90)'"
    try:
        started = executor.dispatch(message('execute_command', command=command))
        identifier = started['command_id']
        assert started['status'] == 'running'
        polled = executor.dispatch(message('execute_command', command=command, command_id=identifier))
        assert 'ready' in polled['output']
        with pytest.raises(BridgeError, match='invalid_arguments'):
            executor.terminal.stop('another-root', identifier)
        stopped = executor.dispatch(message('stop_command', command_id=identifier))
        assert stopped['exit_code'] is not None
    finally:
        executor.terminal.close()
