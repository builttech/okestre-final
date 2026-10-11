"""Single-worker authenticated relay. Payloads and pending calls are memory-only."""
import asyncio
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from contextlib import contextmanager
from pathlib import Path

from pydantic import ValidationError
from starlette.responses import JSONResponse, FileResponse
from starlette.routing import Route, WebSocketRoute
from sqlalchemy.exc import IntegrityError

from gitide_server.database import Project
from okestre_local.protocol import BridgeError, Call, RootInfo, MAX_MESSAGE, OPERATIONS, WRITES, encode, decode


class DeviceStore:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, name TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE, roots TEXT NOT NULL DEFAULT '[]',
                    created REAL NOT NULL, revoked REAL);
                CREATE TABLE IF NOT EXISTS pairing (
                    code_hash TEXT PRIMARY KEY, owner TEXT NOT NULL, name TEXT NOT NULL, expires REAL NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def pair(self, owner, name):
        code = secrets.token_urlsafe(24)
        with self.connect() as db:
            db.execute("DELETE FROM pairing WHERE expires < ? OR owner=?", (time.time(), str(owner)))
            db.execute("INSERT INTO pairing VALUES (?,?,?,?)", (self.digest(code), str(owner), name, time.time() + 300))
        return code

    @staticmethod
    def digest(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def claim(self, code):
        token, identifier = secrets.token_urlsafe(48), uuid.uuid4().hex
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM pairing WHERE code_hash=? AND expires>?", (self.digest(code), time.time())).fetchone()
            if not row:
                raise BridgeError("pairing_invalid_or_expired")
            db.execute("DELETE FROM pairing WHERE code_hash=?", (self.digest(code),))
            db.execute("INSERT INTO devices(id,owner,name,token_hash,created) VALUES (?,?,?,?,?)",
                       (identifier, row["owner"], row["name"], self.digest(token), time.time()))
        return {"device_id": identifier, "token": token}

    def authenticate(self, token):
        with self.connect() as db:
            row = db.execute("SELECT * FROM devices WHERE token_hash=? AND revoked IS NULL", (self.digest(token),)).fetchone()
            return dict(row) if row else None

    def get(self, identifier):
        with self.connect() as db:
            row = db.execute("SELECT * FROM devices WHERE id=? AND revoked IS NULL", (identifier,)).fetchone()
            return dict(row) if row else None

    def roots(self, identifier, roots):
        with self.connect() as db:
            db.execute("UPDATE devices SET roots=? WHERE id=? AND revoked IS NULL", (json.dumps(roots), identifier))

    def revoke(self, identifier, owner):
        with self.connect() as db:
            return db.execute("UPDATE devices SET revoked=? WHERE id=? AND owner=?", (time.time(), identifier, str(owner))).rowcount > 0

    def page(self, owner):
        with self.connect() as db:
            rows = db.execute("SELECT id,name,roots,created,revoked FROM devices WHERE owner=? ORDER BY created DESC LIMIT 100", (str(owner),)).fetchall()
        return [dict(row, roots=json.loads(row["roots"])) for row in rows]


@dataclass
class Channel:
    socket: object
    roots: dict
    pending: dict = field(default_factory=dict)
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    seen: float = field(default_factory=time.monotonic)


class LocalBridge:
    def __init__(self, store, sessions, oauth, timeout=30):
        self.store, self.sessions, self.oauth = store, sessions, oauth
        self.channels = {}
        self.timeout = timeout

    def online(self, identifier):
        channel = self.channels.get(identifier)
        return bool(channel and time.monotonic() - channel.seen < 45)

    def active(self, device):
        return bool(device and self.oauth.active_subject(device["owner"]))

    async def disconnect(self, identifier, code=1000):
        channel = self.channels.pop(identifier, None)
        if channel:
            for future in channel.pending.values():
                if not future.done():
                    future.set_exception(BridgeError("device_disconnected_result_unknown"))
            try:
                await channel.socket.close(code=code)
            except (RuntimeError, OSError):
                pass

    async def websocket(self, socket):
        auth = socket.headers.get("authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else ""
        device = self.store.authenticate(token) if token else None
        # Browser origins have no reason to connect to this device-only endpoint.
        if socket.headers.get("origin") or not self.active(device):
            await socket.close(code=1008)
            return
        identifier = device["id"]
        if identifier in self.channels:
            await socket.close(code=1008)
            return
        await socket.accept()
        channel = None
        try:
            hello = decode(await asyncio.wait_for(socket.receive_text(), 10))
            if hello.get("type") != "hello" or hello.get("version") != 1 or not isinstance(hello.get("roots"), list) or len(hello["roots"]) > 100:
                raise BridgeError("invalid_message")
            roots = [RootInfo.model_validate(r).model_dump() for r in hello["roots"]]
            if len({r["id"] for r in roots}) != len(roots):
                raise BridgeError("invalid_message")
            if identifier in self.channels or not self.active(self.store.get(identifier)):
                raise BridgeError("device_not_authorized")
            channel = Channel(socket, {r["id"]: r for r in roots})
            self.channels[identifier] = channel
            self.store.roots(identifier, roots)
            await socket.send_text(encode({"type": "ready", "version": 1}))
            while True:
                message = decode(await asyncio.wait_for(socket.receive_text(), 45))
                if not self.active(self.store.get(identifier)):
                    break
                channel.seen = time.monotonic()
                if message.get("type") == "ping":
                    async with channel.send_lock:
                        await socket.send_text(encode({"type": "pong"}))
                    continue
                if message.get("type") != "result" or message.get("version") != 1:
                    raise BridgeError("invalid_message")
                future = channel.pending.get(message.get("request_id"))
                if future is not None and not future.done():
                    # Only generic errors cross the server; no arbitrary device text in logs.
                    if message.get("ok") is True and isinstance(message.get("result"), dict):
                        future.set_result(message["result"])
                    else:
                        error = message.get("error")
                        allowed = {"conflict", "read_only", "root_unavailable", "path_blocked", "invalid_path", "unsafe_path", "unsupported_file", "local_access_failed", "invalid_arguments", "request_expired", "mutation_indeterminate", "request_id_conflict", "ambiguous_patch", "inventory_limit", "unsupported_operation", "invalid_task", "ignore_policy_unavailable"}
                        future.set_exception(BridgeError(error if error in allowed else "local_operation_failed"))
        except Exception:
            # Never log frames, arguments, file contents, tokens, or exception bodies.
            pass
        finally:
            if self.channels.get(identifier) is channel and channel is not None:
                await self.disconnect(identifier)
            else:
                try:
                    await socket.close()
                except Exception:
                    pass

    async def request(self, project, operation, arguments, subject, can_write=False):
        if operation not in OPERATIONS:
            raise BridgeError("unsupported_operation_for_local_project")
        device = self.store.get(project.device_id)
        if not self.active(device) or str(subject) != device["owner"]:
            raise BridgeError("device_not_authorized")
        channel = self.channels.get(project.device_id)
        if not self.online(project.device_id):
            raise BridgeError("device_offline")
        root = channel.roots.get(project.root_id)
        if root is None:
            raise BridgeError("root_unavailable")
        if operation in WRITES and not (can_write and root["writable"]):
            raise BridgeError("read_only")
        if len(channel.pending) >= 8:
            raise BridgeError("device_busy")
        identifier = uuid.uuid4().hex
        message = Call(request_id=identifier, root_id=project.root_id, operation=operation,
                       arguments=arguments, can_write=can_write, deadline=time.time() + self.timeout)
        future = asyncio.get_running_loop().create_future()
        channel.pending[identifier] = future
        try:
            async with channel.send_lock:
                await asyncio.wait_for(channel.socket.send_text(encode(message.model_dump())), 5)
            result = await asyncio.wait_for(future, self.timeout)
            if not self.active(self.store.get(project.device_id)):
                raise BridgeError("device_not_authorized")
            return result
        except TimeoutError:
            raise BridgeError("request_timeout_result_unknown" if operation in WRITES else "request_timeout") from None
        finally:
            channel.pending.pop(identifier, None)
            if not future.done():
                future.cancel()

    async def body(self, request):
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > MAX_MESSAGE:
                raise BridgeError("message_too_large")
        return decode(raw.decode("utf-8"))

    async def manage(self, request):
        headers = {"Cache-Control": "no-store"}
        try:
            if request.url.path == "/api/local/claim":
                body = await self.body(request)
                code = body.get("code")
                if not isinstance(code, str) or not 20 <= len(code) <= 100:
                    raise BridgeError("pairing_invalid_or_expired")
                return JSONResponse(self.store.claim(code), headers=headers)
            user = self.oauth.current_user(request)
            if not user or user.role != "root":
                return JSONResponse({"detail": "root_session_required"}, 403, headers=headers)
            csrf = self.oauth.management_csrf(request, user)
            if request.method == "GET":
                items = self.store.page(user.id)
                for item in items:
                    item["online"] = self.online(item["id"]) and item["revoked"] is None
                ids = [i["id"] for i in items]
                with self.sessions() as db:
                    projects = [{"id": p.id, "name": p.name, "device_id": p.device_id, "root_id": p.root_id}
                                for p in db.query(Project).filter(Project.storage_kind == "device", Project.device_id.in_(ids))]
                return JSONResponse({"devices": items, "projects": projects, "csrf_token": csrf}, headers=headers)
            if not hmac.compare_digest(request.headers.get("x-csrf-token", ""), csrf):
                return JSONResponse({"detail": "csrf_invalid"}, 403, headers=headers)
            body = await self.body(request)
            action = request.path_params["action"]
            if action == "pair":
                name = body.get("name", "")
                if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
                    raise BridgeError("invalid_name")
                return JSONResponse({"code": self.store.pair(user.id, name.strip()), "expires_in": 300}, headers=headers)
            if action == "revoke":
                if not self.store.revoke(body.get("device_id"), user.id):
                    raise BridgeError("device_not_authorized")
                await self.disconnect(body["device_id"], 1008)
                return JSONResponse({"status": "revoked"}, headers=headers)
            if action == "bind":
                device = self.store.get(body.get("device_id"))
                if not device or device["owner"] != str(user.id):
                    raise BridgeError("device_not_authorized")
                root = next((r for r in json.loads(device["roots"]) if r["id"] == body.get("root_id")), None)
                name = body.get("name", "")
                if root is None or not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
                    raise BridgeError("invalid_project")
                with self.sessions() as db:
                    existing = db.query(Project).filter_by(device_id=device["id"], root_id=root["id"]).first()
                    if existing:
                        return JSONResponse({"project_id": existing.id}, headers=headers)
                    project = Project(name=name.strip(), path="", storage_kind="device", device_id=device["id"], root_id=root["id"])
                    db.add(project)
                    db.commit()
                    return JSONResponse({"project_id": project.id}, headers=headers)
            if action == "call":
                identifier = body.get("project_id")
                if type(identifier) is not int or not isinstance(body.get("arguments", {}), dict):
                    raise BridgeError("invalid_request")
                with self.sessions() as db:
                    project = db.get(Project, identifier)
                    if not project or project.storage_kind != "device":
                        raise BridgeError("invalid_project")
                    result = await self.request(project, body.get("operation"), body.get("arguments", {}), str(user.id), can_write=True)
                return JSONResponse(result, headers=headers)
            raise BridgeError("unsupported_operation")
        except BridgeError as exc:
            return JSONResponse({"detail": str(exc)}, 400, headers=headers)
        except (ValidationError, ValueError, TypeError, IntegrityError):
            return JSONResponse({"detail": "invalid_request_or_duplicate_project"}, 400, headers=headers)

    def routes(self):
        async def page(request):
            user = self.oauth.current_user(request)
            if not user or user.role != "root":
                return JSONResponse({"detail": "root_session_required"}, 403)
            return FileResponse(Path(__file__).parent / "static" / "local-devices.html", headers={"Cache-Control": "no-store"})
        return [Route("/local-devices", page), Route("/api/local/devices", self.manage),
                Route("/api/local/claim", self.manage, methods=["POST"]),
                Route("/api/local/{action}", self.manage, methods=["POST"]),
                WebSocketRoute("/api/local/connect", self.websocket)]
