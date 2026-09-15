"""Persistent OAuth provider for MCP; protocol validation is handled by the MCP SDK."""
import base64
import hashlib
import hmac
import html
import json
import secrets
import re
import sqlite3
import time
import math
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
from gitide_server.mcp_connections import Connections
from gitide_server.mcp_audit import MCPAudit


class ProjectAuthorizationCode(AuthorizationCode):
    # Missing fields preserve grants issued before project permissions existed.
    project_ids: list[int] | None = None
    can_write: bool = True
    can_execute: bool = False


class ProjectRefreshToken(RefreshToken):
    connection_id: str | None = None
    project_ids: list[int] | None = None
    can_write: bool = True
    can_execute: bool = False


class ProjectAccessToken(AccessToken):
    connection_id: str | None = None
    project_ids: list[int] | None = None
    can_write: bool = True
    can_execute: bool = False


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
    def __init__(self, base_url, store_path, secret, current_user, active_subject, list_projects=None, subject_name=None):
        self.base = base_url.rstrip("/")
        parsed = urlsplit(self.base)
        if (parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"})) or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError("GITIDE_PUBLIC_URL must be an HTTPS origin (HTTP loopback allowed for tests).")
        self.resource = self.base + "/mcp/"
        self.store = OAuthStore(store_path, secret)
        self.secret = secret.encode()
        self.current_user, self.active_subject = current_user, active_subject
        self.list_projects = list_projects or (lambda: [])
        self.subject_name = subject_name or (lambda subject: f"Usuario #{subject}")
        self.connections = Connections(self.store)
        self.audit = MCPAudit(self.store)
        self.import_legacy_connections()

    def import_legacy_connections(self):
        with self.store.connect() as db:
            rows = db.execute("SELECT data FROM oauth WHERE kind='family' AND expires>?", (time.time(),)).fetchall()
        for (encrypted,) in rows:
            pair = json.loads(self.store.cipher.decrypt(encrypted))
            source = self.store.get("refresh", pair["refresh"])
            if source:
                client = self.store.get("client", source["client_id"]) or {}
                self.connections.ensure(pair["family"], source, client.get("client_name") or source["client_id"])

    def token_connection(self, data):
        identifier = data.get("connection_id")
        if not identifier:
            pair = self.store.get("pair", data["token"])
            identifier = self.store.key(pair["family"]) if pair else None
        return identifier

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
        return ProjectAuthorizationCode.model_validate(data) if data and data["client_id"] == client.client_id else None

    def issue(self, source, scopes, family=None):
        if not self.active_subject(source.subject):
            raise TokenError("invalid_grant", "User no longer authorized.")
        access, refresh = secrets.token_urlsafe(48), secrets.token_urlsafe(48)
        family = family or secrets.token_urlsafe(32)
        common = dict(client_id=source.client_id, scopes=scopes, resource=self.resource, subject=source.subject,
                      project_ids=source.project_ids, can_write=source.can_write, can_execute=source.can_execute)
        now = int(time.time())
        client = self.store.get("client", source.client_id) or {}
        identifier = self.connections.ensure(family, dict(common, expires_at=now + 30 * 86400),
            client.get("client_name") or source.client_id, now)
        if not self.connections.allowed(identifier):
            raise TokenError("invalid_grant", "Connection revoked or expired.")
        common["connection_id"] = identifier
        a = ProjectAccessToken(token=access, expires_at=now + 3600, **common)
        r = ProjectRefreshToken(token=refresh, expires_at=now + 30 * 86400, **common)
        self.store.put("access", access, a.model_dump(), a.expires_at)
        self.store.put("refresh", refresh, r.model_dump(), r.expires_at)
        pair = {"access": access, "refresh": refresh, "family": family}
        self.store.put("pair", access, pair, r.expires_at)
        self.store.put("pair", refresh, pair, r.expires_at)
        self.store.put("family", family, pair, r.expires_at)
        self.connections.extend(identifier, r.expires_at)
        return OAuthToken(access_token=access, refresh_token=refresh, token_type="Bearer", expires_in=3600, scope=" ".join(scopes))

    async def exchange_authorization_code(self, client, authorization_code):
        if not self.store.get("code", authorization_code.code, consume=True):
            raise TokenError("invalid_grant", "Code already used or expired.")
        return self.issue(authorization_code, authorization_code.scopes)

    async def load_refresh_token(self, client, refresh_token):
        data = self.store.get("refresh", refresh_token)
        if data and not self.connections.allowed(self.token_connection(data)):
            return None
        used = self.store.get("used_refresh", refresh_token)
        if not data and used and used["client_id"] == client.client_id:
            self.connections.revoke(self.store.key(used["family"]))
            pair = self.store.get("family", used["family"])
            if pair:
                for kind in ("access", "refresh"):
                    self.store.get(kind, pair[kind], consume=True)
        return ProjectRefreshToken.model_validate(data) if data and data["client_id"] == client.client_id else None

    async def exchange_refresh_token(self, client, refresh_token, scopes):
        pair = self.store.get("pair", refresh_token.token)
        if not self.store.get("refresh", refresh_token.token, consume=True):
            raise TokenError("invalid_grant", "Refresh token already used or expired.")
        family = pair["family"] if pair else secrets.token_urlsafe(32)
        self.store.put("used_refresh", refresh_token.token,
            {"family": family, "client_id": client.client_id}, time.time() + 30 * 86400)
        await self.revoke_token(refresh_token, connection=False)
        return self.issue(refresh_token, scopes, family)

    async def load_access_token(self, token):
        data = self.store.get("access", token)
        if data and data["resource"] == self.resource and "mcp" in data["scopes"] and self.active_subject(data["subject"]):
            identifier = self.token_connection(data)
            if not self.connections.allowed(identifier):
                return None
            self.connections.touch(identifier)
            data["connection_id"] = identifier
            return ProjectAccessToken.model_validate(data)
        return None

    async def revoke_token(self, token, connection=True):
        pair = self.store.get("pair", token.token, consume=True)
        if pair:
            if connection:
                self.connections.revoke(self.store.key(pair["family"]))
            for kind in ("access", "refresh"):
                self.store.get(kind, pair[kind], consume=True)
                self.store.get("pair", pair[kind], consume=True)

    def management_csrf(self, request, user):
        session = request.cookies.get("gitide_session", "")
        return hmac.new(self.secret, f"connections:{user.id}:{session}".encode(), hashlib.sha256).hexdigest()

    async def manage_connections(self, request):
        user = self.current_user(request)
        headers = {"Cache-Control": "no-store"}
        if not user or user.role != "root":
            return JSONResponse({"detail": "Acesso restrito ao usuario root."}, 403 if user else 401, headers=headers)
        csrf = self.management_csrf(request, user)
        if request.method == "POST":
            if not hmac.compare_digest(request.headers.get("x-csrf-token", ""), csrf):
                return JSONResponse({"detail": "Autorizacao invalida. Atualize a lista."}, 403, headers=headers)
            identifier = request.path_params["connection_id"]
            if not self.connections.revoke(identifier):
                return JSONResponse({"detail": "Conexao nao encontrada."}, 404, headers=headers)
            return JSONResponse({"status": "revoked"}, headers=headers)
        try:
            offset = int(request.query_params.get("offset", "0"))
            limit = int(request.query_params.get("limit", "50"))
            if offset < 0 or not 1 <= limit <= 100:
                raise ValueError()
        except ValueError:
            return JSONResponse({"detail": "Paginacao invalida."}, 400, headers=headers)
        page = self.connections.page(offset, limit, request.query_params.get("connection_id") or None)
        projects = {p["id"]: p["name"] for p in self.list_projects()}
        for item in page["items"]:
            item["account"] = self.subject_name(item.pop("subject"))
            item["projects"] = None if item["project_ids"] is None else [
                {"id": pid, "name": projects.get(pid, f"Projeto #{pid} (indisponivel)")} for pid in item["project_ids"]]
        return JSONResponse(dict(page, csrf_token=csrf), headers=headers)

    async def audit_history(self, request):
        user = self.current_user(request)
        headers = {"Cache-Control": "no-store"}
        if not user or user.role != "root":
            return JSONResponse({"detail": "Acesso restrito ao usuario root."}, 403 if user else 401, headers=headers)
        params = request.query_params
        try:
            filters = {"offset": int(params.get("offset", 0)), "limit": int(params.get("limit", 25))}
            if filters["offset"] < 0 or not 1 <= filters["limit"] <= 100:
                raise ValueError()
            for name in ("connection_id", "tool", "outcome"):
                if params.get(name):
                    filters[name] = params[name]
            if "connection_id" in filters and not re.fullmatch(r"[0-9a-f]{64}", filters["connection_id"]):
                raise ValueError()
            if "tool" in filters and not re.fullmatch(r"[a-z_]{1,64}", filters["tool"]):
                raise ValueError()
            if "outcome" in filters and filters["outcome"] not in {"success", "error", "denied"}:
                raise ValueError()
            if params.get("project_id"):
                filters["project_id"] = int(params["project_id"])
                if not 0 < filters["project_id"] <= 2147483647:
                    raise ValueError()
            for name in ("start", "end"):
                if params.get(name):
                    value = float(params[name])
                    if not math.isfinite(value) or value < 0:
                        raise ValueError()
                    filters[name] = value
            if filters.get("start", 0) > filters.get("end", float("inf")):
                raise ValueError()
        except ValueError:
            return JSONResponse({"detail": "Filtros invalidos."}, 400, headers=headers)
        page = self.audit.page(**filters)
        projects = {p["id"]: p["name"] for p in self.list_projects()}
        for item in page["items"]:
            subject = item.pop("subject")
            item["account"] = self.subject_name(subject) if subject else "Chave API global" if item["auth_type"] == "api_key" else "Nao identificado"
            item["project_name"] = projects.get(item["project_id"], f'Projeto #{item["project_id"]}') if item["project_id"] else None
        page["projects"] = [{"id": pid, "name": projects.get(pid, f"Projeto #{pid}")} for pid in page.pop("project_ids")]
        return JSONResponse(page, headers=headers)

    def csrf(self, ticket, nonce, user):
        return hmac.new(self.secret, f"{ticket}:{nonce}:{user.id}".encode(), hashlib.sha256).hexdigest()

    def consent_policy(self, redirect_uri):
        callback = urlsplit(redirect_uri)
        # Only the validated callback origin may receive the form's redirect.
        if callback.scheme not in {"https", "http"} or not re.fullmatch(r"[A-Za-z0-9.\-:\[\]]+", callback.netloc):
            raise ValueError("Invalid callback origin.")
        origin = f"{callback.scheme}://{callback.netloc}"
        return ("default-src 'none'; style-src 'unsafe-inline'; "
                f"form-action 'self' {origin}; frame-ancestors 'none'; base-uri 'none'")

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
        policy = self.consent_policy(pending["params"]["redirect_uri"])
        if request.method == "POST":
            form = await request.form()
            nonce = request.cookies.get("mcp_consent", "")
            if not nonce or not hmac.compare_digest(str(form.get("csrf", "")), self.csrf(ticket, nonce, user)):
                return HTMLResponse("Autorizacao invalida. Reabra a conexao.", 403)
            project_ids, can_write, can_execute = [], False, False
            if form.get("decision") == "allow":
                mode = form.get("access_mode")
                if mode not in {"read", "write"}:
                    return HTMLResponse("Selecione o tipo de acesso.", 400)
                can_write = mode == "write"
                can_execute = form.get("can_execute") == "yes"
                if can_execute and not can_write:
                    return HTMLResponse("Terminal exige permissao de leitura e edicao.", 400)
                if form.get("all_projects") == "yes":
                    project_ids = None
                else:
                    requested = form.getlist("project_ids")
                    valid_ids = {str(p["id"]) for p in self.list_projects()}
                    if not requested or any(value not in valid_ids for value in requested):
                        return HTMLResponse("Selecione pelo menos um projeto disponivel.", 400)
                    project_ids = sorted({int(value) for value in requested})
            pending = self.store.get("pending", ticket, consume=True)
            if not pending:
                return HTMLResponse("Solicitacao expirada.", 400)
            params = AuthorizationParams.model_validate(pending["params"])
            if form.get("decision") != "allow":
                url = construct_redirect_uri(str(params.redirect_uri), error="access_denied", state=params.state)
            else:
                code = secrets.token_urlsafe(32)
                record = ProjectAuthorizationCode(code=code, client_id=pending["client_id"], scopes=["mcp"],
                    expires_at=time.time() + 120, code_challenge=params.code_challenge,
                    redirect_uri=params.redirect_uri, redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                    resource=self.resource, subject=str(user.id), project_ids=project_ids, can_write=can_write, can_execute=can_execute)
                self.store.put("code", code, record.model_dump(mode="json"), record.expires_at)
                url = construct_redirect_uri(str(params.redirect_uri), code=code, state=params.state)
            response = RedirectResponse(url, 303)
            response.delete_cookie("mcp_consent", path="/oauth/consent")
        else:
            client = await self.get_client(pending["client_id"])
            nonce = secrets.token_urlsafe(32)
            label = html.escape(client.client_name or client.client_id)
            callback = html.escape(pending["params"]["redirect_uri"])
            projects_html = "".join(
                f'<label class="project"><input type="checkbox" name="project_ids" value="{int(p["id"])}"> {html.escape(p["name"])} (#{int(p["id"])})</label>'
                for p in self.list_projects())
            response = HTMLResponse(f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Autorizar Act IA</title>
<style>body{{font:16px system-ui;background:#111;color:#eee;margin:0;padding:24px}}main{{max-width:540px;margin:5vh auto}}p{{line-height:1.5;overflow-wrap:anywhere}}button{{padding:12px 20px;margin:8px 8px 0 0;cursor:pointer}}small{{overflow-wrap:anywhere}}fieldset{{margin:16px 0;border:1px solid #555;min-width:0}}label{{display:block;padding:8px 0;overflow-wrap:anywhere}}.projects{{max-height:240px;overflow:auto}}</style>
<main><h1>Autorizar acesso ao Act IA</h1><p>Aplicativo: <strong>{label}</strong></p>
<p>Autorize os projetos e o tipo de acesso desta conexao.</p>
<p>Conta: {html.escape(user.email)}</p><p>Destino informado pelo aplicativo:<br><small>{callback}</small></p>
<form method="post"><input type="hidden" name="csrf" value="{self.csrf(ticket, nonce, user)}">
<fieldset><legend>Acesso</legend>
<label><input type="radio" name="access_mode" value="read" checked> Somente leitura</label>
<label><input type="radio" name="access_mode" value="write"> Leitura e edicao</label></fieldset>
<fieldset><legend>Terminal</legend>
<label><input type="checkbox" name="can_execute" value="yes"> Permitir comandos com aprovacao no painel</label>
<p>Exige leitura e edicao. Comandos usam os privilegios do servidor, podem acessar rede, segredos e arquivos fora do projeto. O diretorio inicial nao e uma sandbox.</p></fieldset>
<fieldset><legend>Projetos</legend><div class="projects">{projects_html}</div>
<label><input type="checkbox" name="all_projects" value="yes"> Todos os projetos, inclusive futuros</label></fieldset>
<button name="decision" value="deny">Cancelar</button><button name="decision" value="allow">Autorizar</button></form></main></html>''')
            response.set_cookie("mcp_consent", nonce, secure=self.base.startswith("https:"), httponly=True,
                                samesite="lax", max_age=600, path="/oauth/consent")
        response.headers.update({"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": policy})
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
        routes.append(Route("/api/mcp/connections", self.manage_connections, methods=["GET"]))
        routes.append(Route("/api/mcp/audit", self.audit_history, methods=["GET"]))
        routes.append(Route("/api/mcp/connections/{connection_id}/revoke", self.manage_connections, methods=["POST"]))
        return routes
