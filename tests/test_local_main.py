"""Import the actual application only in an isolated child user profile."""
import os
import subprocess
import sys


def test_actual_app_guards_legacy_routes_and_mounts_bridge(tmp_path):
    script = r'''
from fastapi.testclient import TestClient
from gitide_server.main import app, SessionLocal, Project, User, sign_session
with SessionLocal() as db:
    user = db.query(User).filter_by(role="root").first()
    cookie = sign_session(user.id)
    project = Project(name="local guarded", path="", storage_kind="device", device_id="a"*32, root_id="b"*32)
    db.add(project)
    db.commit()
    identifier = project.id
with TestClient(app) as client:
    client.cookies.set("gitide_session", cookie)
    result = client.get("/api/projects")
    assert result.status_code == 200, result.text
    assert result.json()[0]["storage_kind"] == "device"
    for method, path in (("get", "/files"), ("get", "/files/export.zip"), ("delete", ""), ("post", "/agent/run")):
        response = getattr(client, method)(f"/api/projects/{identifier}{path}")
        assert response.status_code == 409, response.text
    assert client.get("/diagrams").status_code == 200
    for path in ("/connect-device", "/local-devices"):
        page = client.get(path)
        assert page.status_code == 200
        assert "Okestre Connect" in page.text
        assert page.headers["cache-control"] == "no-store"
    state = client.get("/api/local/devices")
    assert state.status_code == 200, state.text
    csrf = state.json()["csrf_token"]
    response = client.post("/api/local/pair", json={"name":"isolated"}, headers={"x-csrf-token": csrf})
    assert response.status_code == 200, response.text
    code = response.json()["code"]
    client.cookies.clear()
    for path in ("/connect-device", "/local-devices"):
        assert client.get(path, follow_redirects=False).status_code == 303
    assert client.get("/api/local/status", follow_redirects=False).status_code == 401
    assert client.get("/diagrams", follow_redirects=False).status_code == 303
    claim = client.post("/api/local/claim", json={"code":code})
    assert claim.status_code == 200, claim.text
print("actual app isolated smoke OK")
'''
    env = dict(os.environ, USERPROFILE=str(tmp_path), GITIDE_ROOT_EMAIL="test@example.invalid")
    # expanduser uses HOME on POSIX and USERPROFILE on Windows.
    if os.name != "nt":
        env["HOME"] = str(tmp_path)
    result = subprocess.run([sys.executable, "-c", script], env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "actual app isolated smoke OK" in result.stdout
