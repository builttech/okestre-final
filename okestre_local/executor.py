"""Local text operations with local snapshots and durable mutation deduplication."""
import hashlib
import json
import os
import re
import sqlite3
import stat
import threading
import time
import uuid
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, ValidationError, validate_call

from .paths import SafeRoot, BLOCKED_DIRS
from .protocol import Call, BridgeError, MAX_FILE, OPERATIONS, WRITES
from gitide_server.sdd_tasks import TASK_FILE, SDD_TASK_CODE_FRAGMENT, parse_task_line

Positive = Annotated[int, Field(ge=1)]
Offset = Annotated[int, Field(ge=0)]
Limit = Annotated[int, Field(ge=1, le=200)]
Text = Annotated[str, Field(max_length=MAX_FILE)]
checked = validate_call(config={"strict": True})


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Executor:
    def __init__(self, roots, data_dir):
        self.roots = roots
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "history.sqlite3"
        self.lock = threading.Lock()
        with self.database() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS mutations (
                  id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, state TEXT NOT NULL,
                  result TEXT, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS snapshots (
                  id TEXT PRIMARY KEY, root_id TEXT NOT NULL, filepath TEXT NOT NULL,
                  previous BLOB, new_hash TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS activity (
                  id INTEGER PRIMARY KEY, operation TEXT NOT NULL, outcome TEXT NOT NULL, created REAL NOT NULL);
            """)

    @contextmanager
    def database(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def dispatch(self, message):
        try:
            call = Call.model_validate(message)
        except ValidationError:
            raise BridgeError("invalid_request") from None
        with self.lock:
            if call.operation not in OPERATIONS:
                raise BridgeError("unsupported_operation")
            root = self.roots.get(call.root_id)
            if root is None or root.get("paused", False):
                raise BridgeError("root_unavailable")
            if call.operation in WRITES and not (root.get("writable", False) and call.can_write):
                raise BridgeError("read_only")
            self.call, self.root = call, SafeRoot(root["path"])
            self.check_deadline()
            fingerprint = sha(json.dumps([call.root_id, call.operation, call.arguments], sort_keys=True, ensure_ascii=False).encode())
            if call.operation in WRITES:
                with self.database() as db:
                    prior = db.execute("SELECT fingerprint,state,result FROM mutations WHERE id=?", (call.request_id,)).fetchone()
                    if prior:
                        if prior[0] != fingerprint:
                            raise BridgeError("request_id_conflict")
                        if prior[1] == "completed":
                            return json.loads(prior[2])
                        raise BridgeError("mutation_indeterminate")
                    db.execute("INSERT INTO mutations VALUES (?,?,?,NULL,?)", (call.request_id, fingerprint, "started", time.time()))
            outcome = "error"
            try:
                result = getattr(self, call.operation)(**call.arguments)
                if call.operation in WRITES:
                    with self.database() as db:
                        db.execute("UPDATE mutations SET state='completed',result=? WHERE id=?", (json.dumps(result), call.request_id))
                outcome = "success"
                return result
            except (ValidationError, TypeError):
                raise BridgeError("invalid_arguments") from None
            except (UnicodeError, OSError):
                raise BridgeError("local_access_failed") from None
            finally:
                with self.database() as db:
                    db.execute("INSERT INTO activity(operation,outcome,created) VALUES (?,?,?)", (call.operation, outcome, time.time()))
                    db.execute("DELETE FROM activity WHERE id NOT IN (SELECT id FROM activity ORDER BY id DESC LIMIT 1000)")

    def check_deadline(self):
        if not time.time() < self.call.deadline <= time.time() + 120:
            raise BridgeError("request_expired")

    def read_bytes(self, path, missing=False):
        self.root.allowed(path)
        try:
            return self.root.read(path)
        except OSError as exc:
            if missing and (isinstance(exc, FileNotFoundError) or (os.name == "nt" and exc.errno in (2, 3))):
                return None
            raise

    def inventory(self):
        items, pending, visited = [], [""], 0
        while pending:
            self.check_deadline()
            folder = pending.pop()
            # Pin ancestors during enumeration, and never follow reparse points.
            with self.root.parent((folder + "/" if folder else "") + "listing", policy=False) as (parent, _):
                with os.scandir(parent) as entries:
                    for entry in entries:
                        visited += 1
                        if visited > 20000:
                            raise BridgeError("inventory_limit")
                        self.check_deadline()
                        path = (folder + "/" if folder else "") + entry.name
                        info = entry.stat(follow_symlinks=False)
                        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                            continue
                        try:
                            self.root.allowed(path)
                        except BridgeError:
                            continue
                        if stat.S_ISDIR(info.st_mode):
                            if entry.name.casefold() not in BLOCKED_DIRS:
                                pending.append(path)
                        elif stat.S_ISREG(info.st_mode):
                            try:
                                with self.root.open_file(path) as stream:
                                    info = os.fstat(stream.fileno())
                            except (BridgeError, OSError):
                                continue
                            items.append({"path": path, "size": info.st_size,
                                          "last_modified": datetime.fromtimestamp(info.st_mtime).isoformat()})
        return sorted(items, key=lambda i: i["path"])

    @checked
    def list_files(self, query: str = "", offset: Offset = 0, limit: Limit = 100) -> dict:
        items = [i for i in self.inventory() if query.casefold() in i["path"].casefold()]
        return {"items": items[offset:offset + limit], "total": len(items), "next_offset": offset + limit if offset + limit < len(items) else None}

    @checked
    def read_file(self, filepath: str, start_line: Positive = 1, limit: Limit = 200) -> dict:
        data = self.read_bytes(filepath)
        lines = data.decode("utf-8").splitlines(keepends=True)
        selected = lines[start_line - 1:start_line - 1 + limit]
        end = start_line - 1 + len(selected)
        return {"filepath": filepath, "content": "".join(selected), "sha256": sha(data),
                "total_lines": len(lines), "start_line": start_line, "end_line": end,
                "next_line": end + 1 if end < len(lines) else None}

    @checked
    def search_files(self, query: Annotated[str, Field(min_length=1, max_length=500)], path_filter: str = "",
                     case_sensitive: bool = False, offset: Offset = 0, limit: Limit = 50) -> dict:
        if "\n" in query or "\r" in query:
            raise BridgeError("invalid_arguments")
        items, seen, skipped = [], 0, 0
        needle = query if case_sensitive else query.casefold()
        for item in self.inventory():
            self.check_deadline()
            if path_filter.casefold() not in item["path"].casefold():
                continue
            try:
                data = self.read_bytes(item["path"]).decode("utf-8")
            except (BridgeError, OSError, UnicodeError):
                skipped += 1
                continue
            for number, line in enumerate(data.splitlines(), 1):
                if needle in (line if case_sensitive else line.casefold()):
                    if seen >= offset:
                        if len(items) == limit:
                            return {"items": items, "next_offset": offset + limit, "skipped_files": skipped}
                        items.append({"filepath": item["path"], "line": number, "snippet": line[:240], "snippet_truncated": len(line) > 240})
                    seen += 1
        return {"items": items, "next_offset": None, "skipped_files": skipped}

    def save(self, filepath, content, expected_sha256):
        data = content.encode("utf-8")
        if len(data) > MAX_FILE or b"\x00" in data:
            raise BridgeError("unsupported_file")
        self.check_deadline()
        previous = self.read_bytes(filepath, missing=True)
        digest = sha(previous) if previous is not None else "missing"
        if expected_sha256 != digest:
            raise BridgeError("conflict")
        snapshot = uuid.uuid4().hex
        with self.database() as db:
            db.execute("INSERT INTO snapshots VALUES (?,?,?,?,?,?)", (snapshot, self.call.root_id, filepath, previous, sha(data), time.time()))
        # Parent must exist. No implicit creation of nested directories by remote calls.
        with self.root.parent(filepath) as (parent, leaf):
            temporary = ".okestre-" + uuid.uuid4().hex + ".tmp"
            kwargs = {} if os.name == "nt" else {"dir_fd": parent}
            temp_path = parent / temporary if os.name == "nt" else temporary
            target_path = parent / leaf if os.name == "nt" else leaf
            fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, **kwargs)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                self.check_deadline()
                # Recheck immediately before replacement; external editors aren't locked.
                latest = self.read_bytes(filepath, missing=True)
                if (sha(latest) if latest is not None else "missing") != digest:
                    raise BridgeError("conflict")
                if os.name == "nt":
                    os.replace(temp_path, target_path)
                else:
                    if previous is not None:
                        mode = os.stat(leaf, dir_fd=parent, follow_symlinks=False).st_mode & 0o777
                        os.chmod(temporary, mode, dir_fd=parent)
                    os.replace(temporary, leaf, src_dir_fd=parent, dst_dir_fd=parent)
                    os.fsync(parent)
            finally:
                try:
                    os.unlink(temp_path, **kwargs)
                except FileNotFoundError:
                    pass
        return {"status": "success", "action": "created" if previous is None else "updated", "snapshot_id": snapshot, "sha256": sha(data)}

    @checked
    def write_file(self, filepath: str, content: Text, expected_sha256: str) -> dict:
        return self.save(filepath, content, expected_sha256)

    @checked
    def patch_file(self, filepath: str, expected_sha256: str,
                   target_content: Annotated[str, Field(min_length=1, max_length=MAX_FILE)],
                   replacement_content: Text, allow_multiple: bool = False) -> dict:
        content = self.read_bytes(filepath).decode("utf-8")
        count = content.count(target_content)
        if not count or (count > 1 and not allow_multiple):
            raise BridgeError("ambiguous_patch")
        return dict(self.save(filepath, content.replace(target_content, replacement_content), expected_sha256), replacements=count)

    @staticmethod
    def requirement_path(path):
        parts = path.replace("\\", "/").split("/")
        return len(parts) >= 3 and parts[0] == ".documents" and parts[1] in {
            "requirements", "functional-requirements", "spec", "specs"} and path.endswith(".md") and ".." not in parts

    @checked
    def list_requirements(self, query: str = "", offset: Offset = 0, limit: Limit = 100) -> dict:
        items = [i for i in self.inventory() if self.requirement_path(i["path"]) and query.casefold() in i["path"].casefold()]
        return {"items": items[offset:offset + limit], "total": len(items), "next_offset": offset + limit if offset + limit < len(items) else None}

    @checked
    def read_requirement(self, filepath: str, start_line: Positive = 1, limit: Limit = 200) -> dict:
        if not self.requirement_path(filepath):
            raise BridgeError("invalid_path")
        return self.read_file(filepath, start_line, limit)

    @checked
    def list_tasks(self, status: Literal["all", "pending", "completed"] = "all", offset: Offset = 0, limit: Limit = 100) -> dict:
        data = self.read_bytes(TASK_FILE, missing=True)
        items = [task for i, line in enumerate((data or b"").decode().splitlines()) if (task := parse_task_line(line, i))]
        items = [t for t in items if status == "all" or t["checked"] == (status == "completed")]
        return {"filepath": TASK_FILE, "sha256": sha(data) if data is not None else "missing", "items": items[offset:offset + limit], "total": len(items), "next_offset": offset + limit if offset + limit < len(items) else None}

    def change_task(self, code, expected_sha256, title=None, checked=False):
        code = code.upper()
        if not re.fullmatch(SDD_TASK_CODE_FRAGMENT, code):
            raise BridgeError("invalid_arguments")
        content = (self.read_bytes(TASK_FILE, missing=True) or b"").decode()
        lines = content.splitlines(keepends=True)
        matches = [i for i, line in enumerate(lines) if (task := parse_task_line(line, i)) and task["code"] == code]
        if title is not None:
            if matches or not title.strip() or any(c in title for c in "\r\n\x00"):
                raise BridgeError("invalid_task")
            updated = content + ("\n" if content and not content.endswith("\n") else "") + f"- [ ] {code}: - {title.strip()}\n"
        else:
            if len(matches) != 1:
                raise BridgeError("invalid_task")
            lines[matches[0]] = re.sub(r"\[[ xX]\]", "[x]" if checked else "[ ]", lines[matches[0]], count=1)
            updated = "".join(lines)
        return dict(self.save(TASK_FILE, updated, expected_sha256), code=code, checked=False if title is not None else checked)

    @checked
    def create_task(self, code: str, title: Annotated[str, Field(min_length=1, max_length=500)], expected_sha256: str) -> dict:
        return self.change_task(code, expected_sha256, title=title)

    @checked
    def update_task(self, code: str, checked: bool, expected_sha256: str) -> dict:
        return self.change_task(code, expected_sha256, checked=checked)
