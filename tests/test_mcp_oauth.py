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
from gitide_server.mcp_server import create_mcp


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
        _, transport, lifespan = create_mcp(validate, metadata_url="http://localhost/.well-known/oauth-protected-resource/mcp/")
        app = FastAPI(lifespan=lifespan)
        app.router.routes.extend(self.provider.routes())
        app.mount("/mcp", transport)
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
        csrf = re.search(r'name="csrf" value="([^"]+)"', page.text).group(1)
        result = self.client.post(location, data={"csrf": csrf, "decision": decision})
        self.assertEqual(result.status_code, 303, result.text)
        return parse_qs(urlsplit(result.headers["location"]).query)

    def exchange(self, code, **overrides):
        data = dict(self.credentials, grant_type="authorization_code", code=code,
                    redirect_uri=self.callback, code_verifier=self.verifier, resource=self.provider.resource)
        data.update(overrides)
        return self.client.post("/token", data=data)

    def test_discovery_and_consent_security(self):
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
