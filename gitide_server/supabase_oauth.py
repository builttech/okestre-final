"""Outbound Supabase OAuth; unrelated to the inbound ChatGPT MCP OAuth provider."""
import base64
import hashlib
import hmac
import json
import re
import secrets
import time
from urllib.parse import urlencode, urlsplit

import requests
from pglast.parser import parse_sql_json
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route


class SupabaseOAuthError(ValueError):
    pass


class OAuthIntegrationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    account_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    project_ref: str = Field(pattern=r"^[a-z0-9]{1,64}$")
    permission: Literal["read", "write", "full"] = "read"
    project_ids: list[int] = Field(min_length=1, max_length=1000)
    enabled: bool = True
    require_approval: bool = True


class SupabaseOAuth:
    def __init__(self, store, base_url, client_id="", client_secret="", request=requests.request):
        self.store, self.client_id, self.client_secret, self.request = store, client_id, client_secret, request
        self.callback_url = base_url.rstrip("/") + "/api/integrations/supabase/callback"
        parsed = urlsplit(base_url)
        if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}):
            raise ValueError("Supabase OAuth requires HTTPS or local loopback.")
        with store.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS supabase_accounts (id TEXT PRIMARY KEY, owner TEXT NOT NULL, data BLOB NOT NULL)")

    @property
    def configured(self):
        return bool(self.client_id and self.client_secret)

    def encode(self, data):
        return self.store.cipher.encrypt(json.dumps(data).encode())

    def decode(self, data):
        return json.loads(self.store.cipher.decrypt(data))

    def metadata(self, owner):
        with self.store.connect() as db:
            accounts = [{"id": row[0], "connected_at": self.decode(row[1])["connected_at"]}
                        for row in db.execute("SELECT id,data FROM supabase_accounts WHERE owner=? ORDER BY rowid DESC", (str(owner),))]
        return {"configured": self.configured, "callback_url": self.callback_url, "accounts": accounts}

    def start(self, owner, session_binding):
        if not self.configured:
            raise SupabaseOAuthError("Configure SUPABASE_OAUTH_CLIENT_ID e SUPABASE_OAUTH_CLIENT_SECRET no servidor.")
        state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
        self.store.put("supabase_state", state, {"owner": str(owner), "binding": session_binding, "verifier": verifier}, time.time() + 600)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        return "https://api.supabase.com/v1/oauth/authorize?" + urlencode({"client_id": self.client_id,
            "redirect_uri": self.callback_url, "response_type": "code", "state": state,
            "code_challenge": challenge, "code_challenge_method": "S256"})

    def http(self, method, path, **kwargs):
        try:
            with self.request(method, "https://api.supabase.com" + path, timeout=(8, 25),
                              allow_redirects=False, stream=True, **kwargs) as response:
                if not 200 <= response.status_code < 300:
                    messages = {401: "Autorizacao Supabase expirada ou revogada. Conecte novamente.",
                                403: "Acesso recusado pelo Supabase. Confira os escopos do OAuth App e autorize novamente.",
                                429: "Limite de chamadas Supabase atingido. Aguarde antes de tentar novamente."}
                    raise SupabaseOAuthError(messages.get(response.status_code, f"Supabase respondeu HTTP {response.status_code}. Verifique o servico; nenhuma repeticao automatica foi feita."))
                data = bytearray()
                for chunk in response.iter_content(8192):
                    data.extend(chunk)
                    if len(data) > 2 * 1024 * 1024:
                        raise SupabaseOAuthError("Resposta Supabase excedeu 2 MiB. Restrinja a consulta; uma escrita pode ja ter sido concluida.")
                return json.loads(data)
        except SupabaseOAuthError:
            raise
        except Exception:
            raise SupabaseOAuthError("Falha de comunicacao com Supabase. Verifique a rede; se houve escrita, confira o banco antes de repetir.") from None

    def exchange(self, fields):
        data = self.http("POST", "/v1/oauth/token", auth=(self.client_id, self.client_secret),
                         headers={"Accept": "application/json"}, data=fields)
        if not isinstance(data, dict) or not isinstance(data.get("access_token"), str) or not isinstance(data.get("refresh_token"), str):
            raise SupabaseOAuthError("Resposta OAuth incompleta. Conecte novamente.")
        try:
            expires = int(data["expires_in"])
            if expires <= 0:
                raise ValueError()
        except (KeyError, TypeError, ValueError):
            raise SupabaseOAuthError("Validade do token Supabase invalida.") from None
        return {"access_token": data["access_token"], "refresh_token": data["refresh_token"], "expires_at": time.time() + expires}

    def finish(self, owner, binding, state, code, denied=False):
        pending = self.store.get("supabase_state", state)
        if not pending or pending["owner"] != str(owner) or not hmac.compare_digest(pending["binding"], binding):
            raise SupabaseOAuthError("Solicitacao OAuth invalida ou expirada. Inicie a conexao novamente.")
        pending = self.store.get("supabase_state", state, consume=True)
        if not pending:
            raise SupabaseOAuthError("Solicitacao OAuth ja utilizada.")
        if denied or not code:
            raise SupabaseOAuthError("Autorizacao Supabase cancelada. Nenhuma conexao foi criada.")
        tokens = self.exchange({"grant_type": "authorization_code", "code": code,
                                "redirect_uri": self.callback_url, "code_verifier": pending["verifier"]})
        identifier = secrets.token_hex(16)
        tokens["connected_at"] = time.time()
        with self.store.connect() as db:
            db.execute("INSERT INTO supabase_accounts VALUES (?,?,?)", (identifier, str(owner), self.encode(tokens)))
        return identifier

    def token(self, identifier, owner=None):
        # Serialize refresh across processes as Supabase rotates refresh tokens.
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT owner,data FROM supabase_accounts WHERE id=?", (identifier,)).fetchone()
            if not row or (owner is not None and row[0] != str(owner)):
                raise SupabaseOAuthError("Conta Supabase desconectada ou indisponivel.")
            data = self.decode(row[1])
            if data["expires_at"] < time.time() + 60:
                refreshed = self.exchange({"grant_type": "refresh_token", "refresh_token": data["refresh_token"]})
                data.update(refreshed)
                db.execute("UPDATE supabase_accounts SET data=? WHERE id=?", (self.encode(data), identifier))
            return data["access_token"]

    def projects(self, identifier, owner):
        data = self.http("GET", "/v1/projects", headers={"Authorization": "Bearer " + self.token(identifier, owner), "Accept": "application/json"})
        if not isinstance(data, list):
            raise SupabaseOAuthError("Lista de projetos Supabase invalida.")
        projects = []
        for item in data:
            ref = item.get("ref") or item.get("id")
            if isinstance(ref, str) and re.fullmatch(r"[a-z0-9]{1,64}", ref):
                projects.append({"ref": ref, "name": str(item.get("name") or ref), "status": str(item.get("status") or ""), "region": str(item.get("region") or "")})
        return projects

    def disconnect(self, identifier, owner):
        with self.store.connect() as db:
            return db.execute("DELETE FROM supabase_accounts WHERE id=? AND owner=?", (identifier, str(owner))).rowcount == 1

    def query(self, config, sql, level, limit=200):
        if not re.fullmatch(r"[a-z0-9]{1,64}", config["project_ref"]):
            raise SupabaseOAuthError("Referencia de projeto Supabase invalida.")
        statement = json.loads(parse_sql_json(sql))["stmts"][0]["stmt"]
        created = statement.get("CreateStmt", {}).get("relation")
        table_as = statement.get("CreateTableAsStmt", {})
        if table_as.get("objtype") == "OBJECT_TABLE":
            created = table_as.get("into", {}).get("rel")
        created = created or statement.get("SelectStmt", {}).get("intoClause", {}).get("rel")
        if created:
            if not created.get("schemaname") or created.get("relpersistence") == "t":
                raise SupabaseOAuthError("No OAuth, crie tabelas permanentes com schema explicito, por exemplo public.minha_tabela.")
            schema = '"' + created['schemaname'].replace('"', '""') + '"'
            table = '"' + created['relname'].replace('"', '""') + '"'
            # One remote request keeps table creation and RLS activation in the same transaction.
            sql = f"BEGIN; SET LOCAL statement_timeout = '15s';\n{sql}\n;\nALTER TABLE {schema}.{table} ENABLE ROW LEVEL SECURITY; COMMIT;"
        data = self.http("POST", f'/v1/projects/{config["project_ref"]}/database/query',
            headers={"Authorization": "Bearer " + self.token(config["account_id"]), "Accept": "application/json"},
            json={"query": sql, "read_only": level == "read"})
        if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
            raise SupabaseOAuthError("Formato de resultado SQL inesperado. Confira o banco antes de repetir uma escrita.")
        columns = list(data[0]) if data else []
        rows, size, truncated = [], 0, len(data) > limit
        for row in data[:limit]:
            values = [None if row.get(key) is None else str(row[key]) for key in columns]
            size += len(json.dumps(values).encode())
            if size > 64000:
                truncated = True
                break
            rows.append(values)
        return {"columns": columns, "rows": rows, "truncated": truncated, "affected_rows": None}


def routes(provider, integrations, oauth):
    async def handle(request):
        user = oauth.current_user(request)
        headers = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
        if not user or user.role != "root":
            return JSONResponse({"detail": "Entre como root para conectar o Supabase."}, 403 if user else 401, headers=headers)
        binding = oauth.management_csrf(request, user)
        if request.method != "GET" and not hmac.compare_digest(request.headers.get("x-csrf-token", ""), binding):
            return JSONResponse({"detail": "Atualize a tela antes de continuar."}, 403, headers=headers)
        action = request.path_params["action"]
        try:
            if action == "callback" and request.method == "GET":
                await run_in_threadpool(provider.finish, user.id, binding, request.query_params.get("state", ""),
                    request.query_params.get("code", ""), "error" in request.query_params)
                return RedirectResponse("/?supabase=connected", 303, headers=headers)
            if action == "start" and request.method == "POST":
                return JSONResponse({"authorize_url": provider.start(user.id, binding)}, headers=headers)
            if action == "projects" and request.method == "GET":
                items = await run_in_threadpool(provider.projects, request.query_params.get("account_id", ""), user.id)
                return JSONResponse({"items": items}, headers=headers)
            if request.method == "POST" and action in {"bind", "disconnect"}:
                if len(await request.body()) > 32000:
                    raise SupabaseOAuthError("Formulario muito grande.")
                data = await request.json()
                if action == "disconnect":
                    await run_in_threadpool(integrations.disconnect_supabase, data.get("account_id", ""), user.id)
                    return JSONResponse({"status": "disconnected"}, headers=headers)
                identifier = data.pop("id", None)
                config = OAuthIntegrationConfig.model_validate(data).model_dump()
                available = await run_in_threadpool(provider.projects, config["account_id"], user.id)
                if config["project_ref"] not in {p["ref"] for p in available}:
                    raise SupabaseOAuthError("Projeto nao disponivel nesta autorizacao Supabase.")
                valid_projects = {p["id"] for p in oauth.list_projects()}
                result = await run_in_threadpool(integrations.save_oauth, config, valid_projects, identifier)
                return JSONResponse(result, headers=headers)
            return JSONResponse({"detail": "Operacao nao encontrada."}, 404, headers=headers)
        except SupabaseOAuthError as error:
            return JSONResponse({"detail": str(error)}, 400, headers=headers)
        except Exception:
            return JSONResponse({"detail": "Nao foi possivel concluir a conexao. Confira os campos e tente novamente."}, 400, headers=headers)
    return [Route("/api/integrations/supabase/{action}", handle, methods=["GET", "POST"])]
