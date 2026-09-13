"""Persistent OAuth provider for MCP; protocol validation is handled by the MCP SDK."""
import base64
import hashlib
import hmac
import html
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from urllib.parse import urlencode, urlsplit

from cryptography.fernet import Fernet
from mcp.server.auth.provider import (AccessToken, AuthorizationCode, AuthorizationParams,
    RefreshToken, RegistrationError, AuthorizeError, TokenError, construct_redirect_uri)
from mcp.server.auth.routes import create_auth_routes, create_protected_resource_routes
from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
from mcp.server.auth.handlers.token import TokenHandler
from mcp.server.auth.middleware.client_auth import ClientAuthenticator
from mcp.server.transport_security import RequestBodyLimitMiddleware
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyHttpUrl
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.routing import Route


class ResourceTokenHandler(TokenHandler):
    def __init__(self, provider):
        super().__init__(provider, ClientAuthenticator(provider))
        self.resource = provider.resource

    async def handle(self, request):
        form = await request.form()
        if form.get("resource") not in (None, self.resource, self.resource.rstrip("/")):
            return JSONResponse({"error": "invalid_target"}, 400,
                                headers={"Cache-Control": "no-store"})
        return await super().handle(request)


class OAuthStore:
    def __init__(self, path, secret):
        self.path = str(path)
        self.cipher = Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()))
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS oauth (kind TEXT, key TEXT, data BLOB, expires REAL, PRIMARY KEY(kind,key))")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            with db:
                yield db
        finally:
            db.close()

    def key(self, value):
        return hashlib.sha256(value.encode()).hexdigest()

    def put(self, kind, key, value, expires):
        data = self.cipher.encrypt(json.dumps(value).encode())
        with self.connect() as db:
            db.execute("DELETE FROM oauth WHERE expires < ?", (time.time(),))
            db.execute("INSERT OR REPLACE INTO oauth VALUES (?,?,?,?)", (kind, self.key(key), data, expires))

    def get(self, kind, key, consume=False):
        with self.connect() as db:
            if consume:
                db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT data,expires FROM oauth WHERE kind=? AND key=?", (kind, self.key(key))).fetchone()
            if consume:
                db.execute("DELETE FROM oauth WHERE kind=? AND key=?", (kind, self.key(key)))
        if not row or row[1] <= time.time():
            return None
        return json.loads(self.cipher.decrypt(row[0]))


class MCPOAuth:
    def __init__(self, base_url, store_path, secret, current_user, active_subject):
        self.base = base_url.rstrip("/")
        parsed = urlsplit(self.base)
        if (parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"})) or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError("GITIDE_PUBLIC_URL must be an HTTPS origin (HTTP loopback allowed for tests).")
        self.resource = self.base + "/mcp/"
        self.store = OAuthStore(store_path, secret)
        self.secret = secret.encode()
        self.current_user, self.active_subject = current_user, active_subject

    async def get_client(self, client_id):
        data = self.store.get("client", client_id)
        return OAuthClientInformationFull.model_validate(data) if data else None

    async def register_client(self, client_info):
        for uri in client_info.redirect_uris or []:
            url = urlsplit(str(uri))
            if url.fragment or url.username or (url.scheme != "https" and not (url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1"})):
                raise RegistrationError("invalid_redirect_uri", "Use HTTPS or a loopback callback.")
        self.store.put("client", client_info.client_id, client_info.model_dump(mode="json"), time.time() + 365 * 86400)

    async def authorize(self, client, params):
        if params.resource not in (None, self.resource, self.resource.rstrip("/")):
            raise AuthorizeError("invalid_request", "Invalid MCP resource.")
        if params.scopes and set(params.scopes) != {"mcp"}:
            raise AuthorizeError("invalid_scope", "Supported scope: mcp.")
        ticket = secrets.token_urlsafe(32)
        self.store.put("pending", ticket, {"client_id": client.client_id,
            "params": params.model_dump(mode="json")}, time.time() + 600)
        return self.base + "/oauth/consent?" + urlencode({"ticket": ticket})

    async def load_authorization_code(self, client, authorization_code):
        data = self.store.get("code", authorization_code)
        return AuthorizationCode.model_validate(data) if data and data["client_id"] == client.client_id else None

    def issue(self, source, scopes, family=None):
        if not self.active_subject(source.subject):
            raise TokenError("invalid_grant", "User no longer authorized.")
        access, refresh = secrets.token_urlsafe(48), secrets.token_urlsafe(48)
        family = family or secrets.token_urlsafe(32)
        common = dict(client_id=source.client_id, scopes=scopes, resource=self.resource, subject=source.subject)
        now = int(time.time())
        a = AccessToken(token=access, expires_at=now + 3600, **common)
        r = RefreshToken(token=refresh, expires_at=now + 30 * 86400, **common)
        self.store.put("access", access, a.model_dump(), a.expires_at)
        self.store.put("refresh", refresh, r.model_dump(), r.expires_at)
        pair = {"access": access, "refresh": refresh, "family": family}
        self.store.put("pair", access, pair, r.expires_at)
        self.store.put("pair", refresh, pair, r.expires_at)
        self.store.put("family", family, pair, r.expires_at)
        return OAuthToken(access_token=access, refresh_token=refresh, token_type="Bearer", expires_in=3600, scope=" ".join(scopes))

    async def exchange_authorization_code(self, client, authorization_code):
        if not self.store.get("code", authorization_code.code, consume=True):
            raise TokenError("invalid_grant", "Code already used or expired.")
        return self.issue(authorization_code, authorization_code.scopes)

    async def load_refresh_token(self, client, refresh_token):
        data = self.store.get("refresh", refresh_token)
        used = self.store.get("used_refresh", refresh_token)
        if not data and used and used["client_id"] == client.client_id:
            pair = self.store.get("family", used["family"])
            if pair:
                for kind in ("access", "refresh"):
                    self.store.get(kind, pair[kind], consume=True)
        return RefreshToken.model_validate(data) if data and data["client_id"] == client.client_id else None

    async def exchange_refresh_token(self, client, refresh_token, scopes):
        pair = self.store.get("pair", refresh_token.token)
        if not self.store.get("refresh", refresh_token.token, consume=True):
            raise TokenError("invalid_grant", "Refresh token already used or expired.")
        family = pair["family"] if pair else secrets.token_urlsafe(32)
        self.store.put("used_refresh", refresh_token.token,
            {"family": family, "client_id": client.client_id}, time.time() + 30 * 86400)
        await self.revoke_token(refresh_token)
        return self.issue(refresh_token, scopes, family)

    async def load_access_token(self, token):
        data = self.store.get("access", token)
        if data and data["resource"] == self.resource and "mcp" in data["scopes"] and self.active_subject(data["subject"]):
            return AccessToken.model_validate(data)
        return None

    async def revoke_token(self, token):
        pair = self.store.get("pair", token.token, consume=True)
        if pair:
            for kind in ("access", "refresh"):
                self.store.get(kind, pair[kind], consume=True)
                self.store.get("pair", pair[kind], consume=True)

    def csrf(self, ticket, nonce, user):
        return hmac.new(self.secret, f"{ticket}:{nonce}:{user.id}".encode(), hashlib.sha256).hexdigest()

    async def consent(self, request):
        ticket = request.query_params.get("ticket", "")
        pending = self.store.get("pending", ticket)
        if not pending:
            return HTMLResponse("Solicitacao expirada. Inicie a conexao novamente.", 400)
        user = self.current_user(request)
        if not user:
            return RedirectResponse("/login?" + urlencode({"next": "/oauth/consent?" + urlencode({"ticket": ticket})}), 303)
        if user.role != "root":
            return HTMLResponse("Apenas o usuario root pode autorizar acesso a todos os projetos.", 403)
        if request.method == "POST":
            form = await request.form()
            nonce = request.cookies.get("mcp_consent", "")
            if not nonce or not hmac.compare_digest(str(form.get("csrf", "")), self.csrf(ticket, nonce, user)):
                return HTMLResponse("Autorizacao invalida. Reabra a conexao.", 403)
            pending = self.store.get("pending", ticket, consume=True)
            if not pending:
                return HTMLResponse("Solicitacao expirada.", 400)
            params = AuthorizationParams.model_validate(pending["params"])
            if form.get("decision") != "allow":
                url = construct_redirect_uri(str(params.redirect_uri), error="access_denied", state=params.state)
            else:
                code = secrets.token_urlsafe(32)
                record = AuthorizationCode(code=code, client_id=pending["client_id"], scopes=["mcp"],
                    expires_at=time.time() + 120, code_challenge=params.code_challenge,
                    redirect_uri=params.redirect_uri, redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                    resource=self.resource, subject=str(user.id))
                self.store.put("code", code, record.model_dump(mode="json"), record.expires_at)
                url = construct_redirect_uri(str(params.redirect_uri), code=code, state=params.state)
            response = RedirectResponse(url, 303)
            response.delete_cookie("mcp_consent", path="/oauth/consent")
        else:
            client = await self.get_client(pending["client_id"])
            nonce = secrets.token_urlsafe(32)
            label = html.escape(client.client_name or client.client_id)
            callback = html.escape(pending["params"]["redirect_uri"])
            response = HTMLResponse(f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Autorizar Act IA</title>
<style>body{{font:16px system-ui;background:#111;color:#eee;margin:0;padding:24px}}main{{max-width:540px;margin:10vh auto}}p{{line-height:1.5;overflow-wrap:anywhere}}button{{padding:12px 20px;margin:8px 8px 0 0;cursor:pointer}}small{{overflow-wrap:anywhere}}</style>
<main><h1>Autorizar acesso ao Act IA</h1><p>Aplicativo: <strong>{label}</strong></p>
<p>Esta conexao podera listar todos os projetos, ler arquivos, consultar Git e criar ou editar arquivos em seu nome.</p>
<p>Conta: {html.escape(user.email)}</p><p>Destino informado pelo aplicativo:<br><small>{callback}</small></p>
<form method="post"><input type="hidden" name="csrf" value="{self.csrf(ticket, nonce, user)}">
<button name="decision" value="deny">Cancelar</button><button name="decision" value="allow">Autorizar</button></form></main></html>''')
            response.set_cookie("mcp_consent", nonce, secure=self.base.startswith("https:"), httponly=True,
                                samesite="lax", max_age=600, path="/oauth/consent")
        response.headers.update({"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'"})
        return response

    def routes(self):
        routes = create_auth_routes(self, AnyHttpUrl(self.base),
            client_registration_options=ClientRegistrationOptions(enabled=True, valid_scopes=["mcp"], default_scopes=["mcp"]),
            revocation_options=RevocationOptions(enabled=True))
        resource_routes = create_protected_resource_routes(AnyHttpUrl(self.resource), [AnyHttpUrl(self.base)], scopes_supported=["mcp"])
        routes += resource_routes
        for path in ("/.well-known/oauth-protected-resource/mcp", "/.well-known/oauth-protected-resource"):
            routes.append(Route(path, resource_routes[0].endpoint, methods=["GET", "OPTIONS"]))
        token_route = Route("/token", ResourceTokenHandler(self).handle, methods=["POST"])
        token_route.app = RequestBodyLimitMiddleware(token_route.app, 65536)
        routes = [token_route if route.path == "/token" else route for route in routes]
        routes.append(Route("/oauth/consent", self.consent, methods=["GET", "POST"]))
        return routes
