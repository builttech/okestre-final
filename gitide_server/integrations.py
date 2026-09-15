"""Supabase PostgreSQL integration and single-use SQL approvals."""
import hashlib
import json
import re
import secrets
import threading
import time
from contextlib import closing
from typing import Literal

import psycopg2
from psycopg2 import sql as pgsql
from pglast.parser import parse_sql_json
from pydantic import BaseModel, ConfigDict, Field


class SupabaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    host: str = Field(min_length=1, max_length=255)
    port: Literal[5432, 6543] = 5432
    database: str = Field(default="postgres", min_length=1, max_length=100)
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(default="", max_length=4096)
    permission: Literal["read", "write", "full"] = "read"
    project_ids: list[int] = Field(min_length=1, max_length=1000)
    enabled: bool = True
    require_approval: bool = True


def sql_level(sql):
    if not sql.strip() or len(sql.encode()) > 32000:
        raise ValueError("SQL deve ter entre 1 e 32000 bytes.")
    try:
        statements = json.loads(parse_sql_json(sql))["stmts"]
    except Exception:
        raise ValueError("SQL PostgreSQL invalido.") from None
    if len(statements) != 1:
        raise ValueError("Execute uma instrucao SQL por vez.")
    stmt = statements[0]["stmt"]
    top = next(iter(stmt))
    if top in {"TransactionStmt", "VariableSetStmt", "CopyStmt", "DiscardStmt", "PrepareStmt", "ExecuteStmt"}:
        raise ValueError("Controle de sessao, COPY e transacoes manuais nao sao permitidos.")
    level = "read" if top == "SelectStmt" else "write" if top in {"InsertStmt", "UpdateStmt", "DeleteStmt"} else "full"
    functions = {"count", "sum", "avg", "min", "max", "lower", "upper", "length", "abs", "round", "now", "current_database", "version"}
    def visit(node):
        nonlocal level
        if isinstance(node, list):
            for child in node:
                visit(child)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key.endswith("Stmt") and key not in {"SelectStmt", "InsertStmt", "UpdateStmt", "DeleteStmt"}:
                    level = "full"
                elif key in {"InsertStmt", "UpdateStmt", "DeleteStmt", "lockingClause"} and level == "read":
                    level = "write"
                if key in {"TypeCast", "CollateClause", "intoClause"}:
                    level = "full"
                if key == "FuncCall":
                    names = [part["String"]["sval"] for part in value["funcname"]]
                    if names[-1] not in functions or (len(names) > 1 and names[:-1] != ["pg_catalog"]):
                        level = "full"
                visit(value)
    visit(stmt)
    return level


class Integrations:
    def __init__(self, store, connect=psycopg2.connect):
        self.store, self.connect = store, connect
        self.lock = threading.RLock()
        with store.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS integrations (id TEXT PRIMARY KEY, data BLOB NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS integration_approvals (id TEXT PRIMARY KEY, data BLOB NOT NULL, state TEXT NOT NULL, expires REAL NOT NULL)")

    def encode(self, data):
        return self.store.cipher.encrypt(json.dumps(data).encode())

    def decode(self, data):
        return json.loads(self.store.cipher.decrypt(data))

    def get(self, identifier):
        with self.store.connect() as db:
            row = db.execute("SELECT data FROM integrations WHERE id=?", (identifier,)).fetchone()
        if not row:
            raise ValueError("Integracao nao encontrada.")
        return self.decode(row[0])

    def public(self, config):
        return {key: value for key, value in config.items() if key != "password"}

    def list(self):
        with self.store.connect() as db:
            return [self.public(self.decode(row[0])) for row in db.execute("SELECT data FROM integrations ORDER BY id")]

    def save(self, values, valid_projects, identifier=None):
        config = SupabaseConfig.model_validate(values).model_dump()
        if not re.fullmatch(r"(?:db\.[a-z0-9-]+\.supabase\.co|[a-z0-9-]+\.pooler\.supabase\.com)", config["host"]):
            raise ValueError("Use o host oficial do Supabase, direto ou pooler.")
        if any(pid not in valid_projects for pid in config["project_ids"]):
            raise ValueError("Selecione projetos existentes do Okestre.")
        with self.lock:
            previous = self.get(identifier) if identifier else None
            if not config["password"]:
                config["password"] = previous["password"] if previous else ""
            if not config["password"]:
                raise ValueError("Informe a senha PostgreSQL, nao uma chave de API.")
            identifier = identifier or secrets.token_hex(16)
            config.update(id=identifier, provider="supabase", revision=secrets.token_hex(16))
            with self.store.connect() as db:
                db.execute("INSERT OR REPLACE INTO integrations VALUES (?,?)", (identifier, self.encode(config)))
            return self.public(config)

    def delete(self, identifier):
        with self.lock, self.store.connect() as db:
            db.execute("DELETE FROM integrations WHERE id=?", (identifier,))

    def query(self, config, sql, level, limit=200):
        try:
            with closing(self.connect(host=config["host"], port=config["port"], dbname=config["database"],
                    user=config["username"], password=config["password"], sslmode="verify-full", sslrootcert="system",
                    connect_timeout=8, application_name="okestre-mcp")) as conn:
                conn.set_session(readonly=level == "read", autocommit=False)
                with conn.cursor() as setup:
                    setup.execute("SET LOCAL statement_timeout = '15s'")
                    setup.execute("SET LOCAL lock_timeout = '3s'")
                    setup.execute("SET LOCAL search_path = pg_catalog, public")
                with conn.cursor(name="okestre_read" if level == "read" else None) as cursor:
                    cursor.execute(sql)
                    rows = cursor.fetchmany(limit + 1) if level == "read" or cursor.description else []
                    columns = [column.name for column in cursor.description] if cursor.description else []
                    result = {"columns": columns, "rows": [], "truncated": len(rows) > limit, "affected_rows": cursor.rowcount}
                    size = 0
                    for row in rows[:limit]:
                        values = [None if value is None else str(value) for value in row]
                        size += len(json.dumps(values).encode())
                        if size > 64000:
                            result["truncated"] = True
                            break
                        result["rows"].append(values)
                # New tables must not become publicly writable through the Supabase Data API.
                statement = json.loads(parse_sql_json(sql))["stmts"][0]["stmt"]
                created = statement.get("CreateStmt", {}).get("relation")
                table_as = statement.get("CreateTableAsStmt", {})
                if table_as.get("objtype") == "OBJECT_TABLE":
                    created = table_as.get("into", {}).get("rel")
                created = created or statement.get("SelectStmt", {}).get("intoClause", {}).get("rel")
                if created:
                    with conn.cursor() as security:
                        security.execute(pgsql.SQL("ALTER TABLE {}.{} ENABLE ROW LEVEL SECURITY").format(
                            pgsql.Identifier(created.get("schemaname") or ("pg_temp" if created.get("relpersistence") == "t" else "public")), pgsql.Identifier(created["relname"])))
                conn.commit()
                return result
        except Exception:
            raise ValueError("Falha PostgreSQL: verifique conexao, credenciais, privilegios ou timeout. Detalhes sensiveis foram omitidos.") from None

    def test(self, identifier):
        return self.query(self.get(identifier), "SELECT current_database(), current_user", "read", 1)

    def pending(self):
        with self.store.connect() as db:
            rows = db.execute("SELECT id,data FROM integration_approvals WHERE state='pending' AND expires>?", (time.time(),)).fetchall()
        return [dict(self.decode(data), approval_id=identifier) for identifier, data in rows]

    def decide(self, identifier, approve):
        with self.store.connect() as db:
            return db.execute("UPDATE integration_approvals SET state=? WHERE id=? AND state='pending' AND expires>?",
                              ("approved" if approve else "rejected", identifier, time.time())).rowcount == 1

    def execute(self, identifier, project_id, sql, connection_id, can_write, approval_id=None):
        with self.lock:
            config = self.get(identifier)
            if not config["enabled"] or project_id not in config["project_ids"]:
                raise PermissionError("Integracao desativada ou nao autorizada para este projeto.")
            level = sql_level(sql)
            if (level != "read" and not can_write) or {"read": 0, "write": 1, "full": 2}[level] > {"read": 0, "write": 1, "full": 2}[config["permission"]]:
                raise PermissionError("SQL excede as permissoes da integracao ou conexao MCP.")
            if level != "read" and config["require_approval"]:
                request = dict(integration_id=identifier, project_id=project_id, sql=sql, connection_id=connection_id, revision=config["revision"])
                with self.store.connect() as db:
                    if not approval_id:
                        approval_id = secrets.token_hex(16)
                        db.execute("INSERT INTO integration_approvals VALUES (?,?,?,?)", (approval_id, self.encode(request), "pending", time.time() + 600))
                        return {"status": "pending_approval", "approval_id": approval_id}
                    row = db.execute("SELECT data,state,expires FROM integration_approvals WHERE id=?", (approval_id,)).fetchone()
                    if not row or self.decode(row[0]) != request or row[2] <= time.time():
                        raise ValueError("Aprovacao invalida ou expirada. Solicite novamente.")
                    if row[1] != "approved":
                        return {"status": row[1], "approval_id": approval_id}
                    if db.execute("UPDATE integration_approvals SET state='executed' WHERE id=? AND state='approved'", (approval_id,)).rowcount != 1:
                        raise ValueError("Aprovacao ja consumida.")
            return dict(self.query(config, sql, level), status="completed")
