import base64
import hashlib
import re
import tempfile
import unittest
import asyncio
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from fastapi import FastAPI
from fastapi.testclient import TestClient
from gitide_server.mcp_oauth import MCPOAuth
from gitide_server.mcp_server import create_mcp, mount_mcp


class OAuthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.user = SimpleNamespace(id=1, role="root", email="root@example.test")
        self.provider = MCPOAuth("http://localhost", Path(self.temp.name) / "oauth.db", "test-secret",
            lambda req: self.user if req.cookies.get("login") == "yes" else None,
            lambda subject: bool(self.user and self.user.role == "root" and subject == "1"))
        async def validate(request):
            return await self.provider.load_access_token(request.headers.get("authorization", "").removeprefix("Bearer "))
        _, transport, lifespan = create_mcp(validate, metadata_url="http://localhost/.well-known/oauth-protected-resource/mcp/", audit=self.provider.audit)
        app = FastAPI(lifespan=lifespan)
        app.router.routes.extend(self.provider.routes())
        mount_mcp(app, transport)
        self.client = TestClient(app, base_url="http://localhost", follow_redirects=False)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.verifier = "v" * 64
        self.callback = "https://chatgpt.com/connector/oauth/test"
        response = self.client.post("/register", json={"client_name": "Test client",
            "redirect_uris": [self.callback], "token_endpoint_auth_method": "client_secret_post",
            "grant_types": ["authorization_code", "refresh_token"], "response_types": ["code"], "scope": "mcp"})
        self.assertEqual(response.status_code, 201, response.text)
        self.credentials = {k: response.json()[k] for k in ("client_id", "client_secret")}

    def authorize(self, **overrides):
        params = dict(client_id=self.credentials["client_id"], redirect_uri=self.callback,
            response_type="code", scope="mcp", state="original-state", resource=self.provider.resource,
            code_challenge=base64.urlsafe_b64encode(hashlib.sha256(self.verifier.encode()).digest()).decode().rstrip("="),
            code_challenge_method="S256")
        params.update(overrides)
        return self.client.get("/authorize", params=params)

    def approve(self, decision="allow"):
        auth = self.authorize()
        self.assertIn(auth.status_code, (302, 303), auth.text)
        location = auth.headers["location"]
        self.client.cookies.set("login", "yes")
        page = self.client.get(location)
        self.assertIn("form-action 'self' https://chatgpt.com;", page.headers["content-security-policy"])
        self.assertIn("frame-ancestors 'none'", page.headers["content-security-policy"])
        csrf = re.search(r'name="csrf" value="([^"]+)"', page.text).group(1)
        result = self.client.post(location, data={"csrf": csrf, "decision": decision,
            "access_mode": "write", "all_projects": "yes"})
        self.assertEqual(result.status_code, 303, result.text)
        self.assertIn("form-action 'self' https://chatgpt.com;", result.headers["content-security-policy"])
        return parse_qs(urlsplit(result.headers["location"]).query)

    def exchange(self, code, **overrides):
        data = dict(self.credentials, grant_type="authorization_code", code=code,
                    redirect_uri=self.callback, code_verifier=self.verifier, resource=self.provider.resource)
        data.update(overrides)
        return self.client.post("/token", data=data)

    def test_discovery_and_consent_security(self):
        for path in ("/.well-known/oauth-protected-resource/mcp", "/.well-known/oauth-protected-resource"):
            result = self.client.get(path)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["resource"], self.provider.resource)
        for method in (self.client.get, self.client.post):
            result = method("/mcp")
            self.assertEqual(result.status_code, 401)
            self.assertNotIn("location", result.headers)
        meta = self.client.get("/.well-known/oauth-authorization-server").json()
        self.assertEqual(meta["code_challenge_methods_supported"], ["S256"])
        self.assertEqual(self.client.get("/.well-known/oauth-protected-resource/mcp/").json()["resource"], self.provider.resource)
        unauthorized = self.client.post("/mcp/", json={})
        self.assertEqual(unauthorized.status_code, 401)
        self.assertIn("resource_metadata", unauthorized.headers["www-authenticate"])
        location = self.authorize().headers["location"]
        self.assertTrue(self.client.get(location).headers["location"].startswith("/login?next="))
        self.client.cookies.set("login", "yes")
        self.assertEqual(self.client.post(location, data={"decision": "allow"}).status_code, 403)
        self.user.role = "member"
        self.assertEqual(self.client.get(location).status_code, 403)

    def test_selected_permissions_survive_refresh(self):
        self.provider.list_projects = lambda: [{"id": 7, "name": "Selected project"}]
        location = self.authorize().headers["location"]
        self.client.cookies.set("login", "yes")
        page = self.client.get(location)
        self.assertIn('value="read" checked', page.text)
        csrf = re.search(r'name="csrf" value="([^"]+)"', page.text).group(1)
        fields = {"csrf": csrf, "decision": "allow", "access_mode": "read"}
        self.assertEqual(self.client.post(location, data=fields).status_code, 400)
        self.assertEqual(self.client.post(location, data=dict(fields, project_ids="999")).status_code, 400)
        accepted = self.client.post(location, data=dict(fields, project_ids="7"))
        code = parse_qs(urlsplit(accepted.headers["location"]).query)["code"][0]
        tokens = self.exchange(code).json()
        access = asyncio.run(self.provider.load_access_token(tokens["access_token"]))
        self.assertEqual(access.project_ids, [7])
        self.assertFalse(access.can_write)
        self.assertFalse(access.can_execute)
        refreshed = self.client.post("/token", data=dict(self.credentials,
            grant_type="refresh_token", refresh_token=tokens["refresh_token"])).json()
        access = asyncio.run(self.provider.load_access_token(refreshed["access_token"]))
        self.assertEqual(access.project_ids, [7])
        self.assertFalse(access.can_write)

    def test_terminal_consent_and_refresh(self):
        location = self.authorize().headers["location"]
        self.client.cookies.set("login", "yes")
        page = self.client.get(location)
        self.assertNotIn('name="can_execute" value="yes" checked', page.text)
        csrf = re.search(r'name="csrf" value="([^"]+)"', page.text).group(1)
        fields = dict(csrf=csrf, decision="allow", access_mode="read", all_projects="yes", can_execute="yes")
        self.assertEqual(self.client.post(location, data=fields).status_code, 400)
        fields["access_mode"] = "write"
        response = self.client.post(location, data=fields)
        code = parse_qs(urlsplit(response.headers["location"]).query)["code"][0]
        tokens = self.exchange(code).json()
        self.assertTrue(asyncio.run(self.provider.load_access_token(tokens["access_token"])).can_execute)
        refreshed = self.client.post("/token", data=dict(self.credentials,
            grant_type="refresh_token", refresh_token=tokens["refresh_token"])).json()
        self.assertTrue(asyncio.run(self.provider.load_access_token(refreshed["access_token"])).can_execute)

    def test_legacy_grant_compatibility(self):
        tokens = self.exchange(self.approve()["code"][0]).json()
        data = self.provider.store.get("access", tokens["access_token"])
        data.pop("project_ids")
        data.pop("can_write")
        self.provider.store.put("access", tokens["access_token"], data, data["expires_at"])
        access = asyncio.run(self.provider.load_access_token(tokens["access_token"]))
        self.assertIsNone(access.project_ids)
        self.assertTrue(access.can_write)

    def test_manage_connection_rotation_and_revocation(self):
        self.assertEqual(self.client.get("/api/mcp/connections").status_code, 401)
        tokens = self.exchange(self.approve()["code"][0]).json()
        page = self.client.get("/api/mcp/connections").json()
        self.assertEqual(page["total"], 1)
        connection = page["items"][0]
        self.assertEqual(connection["status"], "active")
        self.assertIsNone(connection["last_used_at"])
        serialized = str(page)
        for secret in (tokens["access_token"], tokens["refresh_token"], self.credentials["client_secret"]):
            self.assertNotIn(secret, serialized)
        asyncio.run(self.provider.load_access_token(tokens["access_token"]))
        self.assertIsNotNone(self.client.get("/api/mcp/connections").json()["items"][0]["last_used_at"])
        refreshed = self.client.post("/token", data=dict(self.credentials,
            grant_type="refresh_token", refresh_token=tokens["refresh_token"])).json()
        after = self.client.get("/api/mcp/connections").json()
        self.assertEqual(after["total"], 1)
        self.assertEqual(after["items"][0]["id"], connection["id"])
        path = f'/api/mcp/connections/{connection["id"]}/revoke'
        self.assertEqual(self.client.post(path).status_code, 403)
        self.assertEqual(self.client.post(path, headers={"X-CSRF-Token": page["csrf_token"]}).status_code, 200)
        self.assertEqual(self.client.post(path, headers={"X-CSRF-Token": page["csrf_token"]}).status_code, 200)
        self.assertIsNone(asyncio.run(self.provider.load_access_token(refreshed["access_token"])))
        rejected = self.client.post("/token", data=dict(self.credentials,
            grant_type="refresh_token", refresh_token=refreshed["refresh_token"]))
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(self.client.get("/api/mcp/connections").json()["items"][0]["status"], "revoked")
        self.user.role = "member"
        self.assertEqual(self.client.get("/api/mcp/connections").status_code, 403)

    def test_legacy_connections_import(self):
        tokens = self.exchange(self.approve()["code"][0]).json()
        for kind, key in (("access", tokens["access_token"]), ("refresh", tokens["refresh_token"])):
            data = self.provider.store.get(kind, key)
            data.pop("connection_id")
            self.provider.store.put(kind, key, data, data["expires_at"])
        with self.provider.store.connect() as db:
            db.execute("DELETE FROM mcp_connections")
        restored = MCPOAuth(self.provider.base, self.provider.store.path, "test-secret",
            self.provider.current_user, self.provider.active_subject)
        rows = restored.connections.page(0, 10)
        self.assertEqual(rows["total"], 1)
        self.assertIsNone(rows["items"][0]["authorized_at"])
        self.assertIsNotNone(asyncio.run(restored.load_access_token(tokens["access_token"])))
        restored.connections.revoke(rows["items"][0]["id"])
        self.assertIsNone(asyncio.run(restored.load_access_token(tokens["access_token"])))
        restarted = MCPOAuth(self.provider.base, self.provider.store.path, "test-secret",
            self.provider.current_user, self.provider.active_subject)
        self.assertIsNone(asyncio.run(restarted.load_access_token(tokens["access_token"])))

    def test_management_pagination_and_expiration(self):
        tokens = self.exchange(self.approve()["code"][0]).json()
        self.exchange(self.approve()["code"][0])
        first = self.client.get("/api/mcp/connections?limit=1").json()
        self.assertEqual(first["next_offset"], 1)
        second = self.client.get("/api/mcp/connections?limit=1&offset=1").json()
        self.assertNotEqual(first["items"][0]["id"], second["items"][0]["id"])
        self.assertIsNone(second["next_offset"])
        self.assertEqual(self.client.get("/api/mcp/connections?limit=1000").status_code, 400)
        connection_id = asyncio.run(self.provider.load_access_token(tokens["access_token"])).connection_id
        self.provider.connections.extend(connection_id, time.time() - 1)
        statuses = {item["id"]: item["status"] for item in self.client.get("/api/mcp/connections").json()["items"]}
        self.assertEqual(statuses[connection_id], "expired")

    def test_audit_admin_filters(self):
        self.assertEqual(self.client.get("/api/mcp/audit").status_code, 401)
        tokens = self.exchange(self.approve()["code"][0]).json()
        grant = asyncio.run(self.provider.load_access_token(tokens["access_token"]))
        self.provider.audit.record(grant=grant, tool="read_file", project_id=7, outcome="success", duration_ms=12)
        self.provider.audit.record(grant=grant, tool="patch_file", project_id=7, outcome="denied", duration_ms=4)
        page = self.client.get("/api/mcp/audit?limit=1").json()
        self.assertEqual(page["total"], 2)
        self.assertEqual(page["next_offset"], 1)
        self.assertEqual(page["items"][0]["application"], "Test client")
        filtered = self.client.get("/api/mcp/audit", params={"connection_id": grant.connection_id,
            "project_id": 7, "tool": "read_file", "outcome": "success", "start": 0, "end": time.time() + 1}).json()
        self.assertEqual(filtered["total"], 1)
        self.assertEqual(self.client.get("/api/mcp/audit?end=1").json()["total"], 0)
        for query in ("start=nan", "start=10&end=1", "limit=101", "outcome=invalid", "offset=-1"):
            self.assertEqual(self.client.get("/api/mcp/audit?" + query).status_code, 400)
        self.user.role = "member"
        self.assertEqual(self.client.get("/api/mcp/audit").status_code, 403)

    def test_pkce_replay_refresh_revoke_and_mcp(self):
        params = self.approve()
        self.assertEqual(params["state"], ["original-state"])
        code = params["code"][0]
        self.assertEqual(self.exchange(code, code_verifier="wrong").status_code, 400)
        response = self.exchange(code)
        self.assertEqual(response.status_code, 200, response.text)
        tokens = response.json()
        self.assertEqual(self.exchange(code).status_code, 400)
        def mcp(token):
            return self.client.post("/mcp/", headers={"Authorization": "Bearer " + token,
                "Accept": "application/json, text/event-stream"}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual(mcp(tokens["access_token"]).status_code, 200)
        slashless = self.client.post("/mcp", headers={"Authorization": "Bearer " + tokens["access_token"],
            "Accept": "application/json, text/event-stream"}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual(slashless.status_code, 200, slashless.text)
        refreshed = self.client.post("/token", data=dict(self.credentials, grant_type="refresh_token", refresh_token=tokens["refresh_token"]))
        self.assertEqual(refreshed.status_code, 200, refreshed.text)
        self.assertEqual(mcp(tokens["access_token"]).status_code, 401)
        fresh = refreshed.json()
        self.assertEqual(mcp(fresh["access_token"]).status_code, 200)
        self.client.post("/revoke", data=dict(self.credentials, token=fresh["refresh_token"]))
        self.assertEqual(mcp(fresh["access_token"]).status_code, 401)

    def test_refresh_replay_revokes_successor(self):
        original = self.exchange(self.approve()["code"][0]).json()
        data = dict(self.credentials, grant_type="refresh_token", refresh_token=original["refresh_token"])
        fresh = self.client.post("/token", data=data).json()
        self.assertEqual(self.client.post("/token", data=data).status_code, 400)
        self.assertIsNone(asyncio.run(self.provider.load_access_token(fresh["access_token"])))

    def test_denial_redirect_and_audience(self):
        self.assertEqual(self.approve("deny")["error"], ["access_denied"])
        result = self.authorize(redirect_uri="https://evil.example/callback")
        self.assertEqual(result.status_code, 400)
        result = self.authorize(resource="https://other.example/mcp/")
        self.assertNotIn("/oauth/consent", result.headers.get("location", ""))

    def test_persistence_expiry_and_disabled_user(self):
        code = self.approve()["code"][0]
        self.assertEqual(self.exchange(code, resource="https://wrong.example/").status_code, 400)
        tokens = self.exchange(code).json()
        token = tokens["access_token"]
        restored = MCPOAuth(self.provider.base, self.provider.store.path, "test-secret",
                           self.provider.current_user, self.provider.active_subject)
        self.assertIsNotNone(asyncio.run(restored.get_client(self.credentials["client_id"])))
        self.assertIsNotNone(asyncio.run(restored.load_access_token(token)))
        self.user.role = "member"
        self.assertIsNone(asyncio.run(restored.load_access_token(token)))
        self.user.role = "root"
        record = self.provider.store.get("access", token)
        self.provider.store.put("access", token, record, time.time() - 1)
        self.assertIsNone(asyncio.run(restored.load_access_token(token)))
        result = self.authorize(code_challenge_method="plain")
        self.assertNotIn("/oauth/consent", result.headers.get("location", ""))


if __name__ == "__main__":
    unittest.main()
