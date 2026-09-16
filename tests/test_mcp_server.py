import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gitide_server.database import Base, Project, FileSnapshot, ActivityLog, PendingCommand
from gitide_server.mcp_server import create_mcp
from gitide_server.mcp_oauth import OAuthStore
from gitide_server.mcp_connections import Connections
from gitide_server.mcp_audit import MCPAudit
from gitide_server.integrations import Integrations


class MCPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.engine = create_engine("sqlite:///" + str(self.root / "test.db"))
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        (self.workspace / "hello.txt").write_bytes(b"first\nsecond\n")
        with self.sessions() as db:
            db.add(Project(id=1, name="MCP test", path=str(self.workspace)))
            db.commit()
        self.grant = True
        store = OAuthStore(self.root / "audit.db", "test-secret")
        Connections(store)
        self.audit = MCPAudit(store)
        self.integrations = Integrations(store)
        _, transport, lifespan = create_mcp(
            lambda req: self.grant if req.headers.get("authorization") == "Bearer test-token" else False, self.sessions, audit=self.audit, integrations=self.integrations)
        app = FastAPI(lifespan=lifespan)
        app.mount("/mcp", transport)
        self.client = TestClient(app, base_url="http://localhost")
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.engine.dispose()
        self.temp.cleanup()

    def rpc(self, method, params=None, token="test-token", extra_headers=None):
        headers = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-06-18"}
        if token:
            headers["Authorization"] = "Bearer " + token
        headers.update(extra_headers or {})
        return self.client.post("/mcp/", headers=headers, json={
            "jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})

    def tool(self, name, **arguments):
        response = self.rpc("tools/call", {"name": name, "arguments": arguments})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["result"]

    def test_read_large_minified_json_and_utf8(self):
        import hashlib
        import json

        for value in ("x" * 90000, "\u00e1" * 45000):
            content = json.dumps({"template": value}, ensure_ascii=False)
            data = content.encode("utf-8")
            (self.workspace / "template.json").write_bytes(data)
            result = self.tool("read_file", project_id=1, filepath="template.json")["structuredContent"]
            self.assertEqual(result["content"], content)
            self.assertEqual(json.loads(result["content"])["template"], value)
            self.assertEqual(result["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(result["total_lines"], 1)
            self.assertIsNone(result["next_line"])

    def test_read_one_mib_boundary_and_pagination(self):
        content = "x" * (1024 * 1024)
        path = self.workspace / "large.txt"
        path.write_bytes(content.encode())
        result = self.tool("read_file", project_id=1, filepath="large.txt")["structuredContent"]
        self.assertEqual(result["content"], content)
        path.write_bytes((content + "x").encode())
        self.assertTrue(self.tool("read_file", project_id=1, filepath="large.txt")["isError"])
        path.write_bytes(("x" * 90000 + "\nsecond\n").encode())
        result = self.tool("read_file", project_id=1, filepath="large.txt", limit=1)["structuredContent"]
        self.assertEqual(result["content"], "x" * 90000 + "\n")
        self.assertEqual(result["next_line"], 2)
        result = self.tool("read_file", project_id=1, filepath="large.txt", start_line=2, limit=1)["structuredContent"]
        self.assertEqual(result["content"], "second\n")
        self.assertIsNone(result["next_line"])

    def test_auth_and_origin(self):
        for token in (None, "wrong"):
            self.assertEqual(self.rpc("tools/list", token=token).status_code, 401)
        self.assertEqual(self.rpc("tools/list", extra_headers={"Origin": "https://evil.example"}).status_code, 403)

    def test_audit_results_and_private_data(self):
        secret = "SENSITIVE_CONTENT_NOT_FOR_AUDIT"
        (self.workspace / "hello.txt").write_text(secret)
        self.tool("read_file", project_id=1, filepath="hello.txt")
        self.tool("read_file", project_id=1, filepath="missing-secret-name.txt")
        self.grant = SimpleNamespace(project_ids=[1], can_write=False, subject="1", connection_id="a" * 64)
        self.tool("write_file", project_id=1, filepath="hello.txt", content=secret, expected_sha256="private-hash")
        self.tool("read_file", project_id=secret, filepath="hello.txt")
        self.tool(secret)
        self.rpc("tools/call", {"name": "read_file", "arguments": {"project_id": 1}}, token="private-invalid-token")
        rows = self.audit.page()["items"]
        self.assertEqual(len(rows), 6)
        self.assertEqual([item["outcome"] for item in rows], ["denied", "error", "error", "denied", "error", "success"])
        self.assertEqual(rows[3]["connection_id"], "a" * 64)
        self.assertEqual(rows[-1]["auth_type"], "api_key")
        self.assertTrue(all(row["duration_ms"] >= 0 for row in rows))
        content = str(rows)
        for value in (secret, "missing-secret-name.txt", "private-hash", "private-invalid-token"):
            self.assertNotIn(value, content)
        self.assertEqual(self.audit.page(project_id=1, outcome="denied")["total"], 1)
        self.assertEqual(self.audit.page(tool="read_file", limit=1)["next_offset"], 1)

    def test_project_and_write_permissions(self):
        with self.sessions() as db:
            db.add(Project(id=2, name="Other project", path=str(self.workspace)))
            db.commit()
        self.grant = SimpleNamespace(project_ids=[1], can_write=False)
        projects = self.tool("list_projects")["structuredContent"]
        self.assertEqual([p["id"] for p in projects["items"]], [1])
        self.assertEqual(projects["total"], 1)
        self.assertFalse(self.tool("read_file", project_id=1, filepath="hello.txt").get("isError"))
        for name, args in (("read_file", {"filepath": "hello.txt"}),
                           ("list_files", {}), ("search_files", {"query": "first"}),
                           ("git_status", {}), ("git_diff", {"filepath": "hello.txt"})):
            self.assertTrue(self.tool(name, project_id=2, **args)["isError"])
        for name, args in (("write_file", {"content": "blocked"}),
                           ("patch_file", {"target_content": "first", "replacement_content": "blocked"})):
            self.assertTrue(self.tool(name, project_id=1, filepath="hello.txt", expected_sha256="unused", **args)["isError"])
        with self.sessions() as db:
            self.assertEqual(db.query(ActivityLog).count(), 0)
        self.grant = SimpleNamespace(project_ids=[2], can_write=True)
        self.assertEqual(self.tool("list_projects")["structuredContent"]["items"][0]["id"], 2)
        self.grant = True
        self.assertEqual(self.tool("list_projects")["structuredContent"]["total"], 2)

    def test_initialize_and_discovery(self):
        response = self.rpc("initialize", {"protocolVersion": "2025-06-18",
            "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}})
        self.assertEqual(response.status_code, 200)
        self.assertIn("serverInfo", response.json()["result"])
        tools = self.rpc("tools/list").json()["result"]["tools"]
        self.assertEqual({t["name"] for t in tools},
                         {"list_projects", "list_files", "read_file", "write_file", "git_status",
                          "search_files", "patch_file", "git_diff", "list_requirements", "read_requirement",
                          "list_tasks", "create_task", "update_task", "execute_command", "list_integrations", "database_schema", "database_query"})

    def test_database_permissions_and_audit(self):
        from unittest.mock import patch
        config = self.integrations.save(dict(name="Supabase test", host="db.test.supabase.co", username="reader",
            password="private-db-password", project_ids=[1], permission="full"), {1})
        self.grant = SimpleNamespace(project_ids=[1], can_write=False, connection_id="connection")
        items = self.tool("list_integrations", project_id=1)["structuredContent"]
        self.assertNotIn("password", str(items))
        args = dict(project_id=1, integration_id=config["id"])
        with patch.object(self.integrations, "query", return_value={"rows": [["ok"]]}) as query:
            self.assertFalse(self.tool("database_query", **args, sql="SELECT 1").get("isError"))
            self.assertTrue(self.tool("database_query", **args, sql="DELETE FROM public.t")["isError"])
            self.grant.can_write = True
            approval = self.tool("database_query", **args, sql="DELETE FROM public.t")["structuredContent"]
            self.assertEqual(approval["status"], "pending_approval")
            self.integrations.decide(approval["approval_id"], True)
            self.assertFalse(self.tool("database_query", **args, sql="DELETE FROM public.t", approval_id=approval["approval_id"]).get("isError"))
            self.assertEqual(query.call_count, 2)
            self.grant.project_ids = []
            self.assertTrue(self.tool("database_schema", **args)["isError"])
        self.assertNotIn("DELETE", str(self.audit.page()))
        self.assertNotIn("private-db-password", str(self.audit.page()))

    def test_terminal_permission_approval_and_single_use(self):
        from unittest.mock import patch
        args = dict(project_id=1, command="echo MCP-terminal-test")
        for grant in (True, SimpleNamespace(project_ids=[1], can_write=True),
                      SimpleNamespace(project_ids=[1], can_write=False, can_execute=True),
                      SimpleNamespace(project_ids=[], can_write=True, can_execute=True)):
            self.grant = grant
            self.assertTrue(self.tool("execute_command", **args)["isError"])
        self.grant = SimpleNamespace(project_ids=[1], can_write=True, can_execute=True)
        with patch("gitide_server.mcp_terminal.execute", return_value={"exit_code": 0, "output": "OK", "timed_out": False, "truncated": False}) as execute:
            pending = self.tool("execute_command", **args)["structuredContent"]
            self.assertEqual(pending["status"], "pending_approval")
            args["command_id"] = pending["command_id"]
            self.assertEqual(self.tool("execute_command", **args)["structuredContent"]["status"], "pending")
            execute.assert_not_called()
            with self.sessions() as db:
                db.get(PendingCommand, args["command_id"]).status = "approved"
                db.commit()
            self.assertTrue(self.tool("execute_command", **dict(args, command="echo changed"))["isError"])
            self.assertEqual(self.tool("execute_command", **args)["structuredContent"]["status"], "completed")
            self.assertEqual(self.tool("execute_command", **args)["structuredContent"]["status"], "executed")
            execute.assert_called_once_with("echo MCP-terminal-test", str(self.workspace))
        self.assertNotIn("MCP-terminal-test", str(self.audit.page()))

    def test_terminal_runner_limits(self):
        import os
        import shlex
        import subprocess
        import sys
        from gitide_server.mcp_terminal import execute
        def command(script):
            args = [sys.executable, "-c", script]
            return subprocess.list2cmdline(args) if os.name == "nt" else shlex.join(args)
        result = execute(command("print('x' * 100000)"), str(self.workspace), max_output=100)
        self.assertEqual(len(result["output"]), 100)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["exit_code"], 0)
        result = execute(command("import time; time.sleep(10)"), str(self.workspace), timeout=0.3)
        self.assertTrue(result["timed_out"])
        result = execute(command("import sys; sys.exit(3)"), str(self.workspace))
        self.assertEqual(result["exit_code"], 3)

    def test_task_lifecycle_and_conflicts(self):
        empty = self.tool("list_tasks", project_id=1)["structuredContent"]
        self.assertEqual(empty["sha256"], "missing")
        code = "TASK-RF-0001-01-001"
        created = self.tool("create_task", project_id=1, code=code, title="Implement login", expected_sha256="missing")
        self.assertFalse(created.get("isError"), created)
        digest = created["structuredContent"]["sha256"]
        duplicate = self.tool("create_task", project_id=1, code=code, title="Duplicate", expected_sha256=digest)
        self.assertTrue(duplicate["isError"])
        self.assertTrue(self.tool("update_task", project_id=1, code=code, checked=True, expected_sha256="stale")["isError"])
        updated = self.tool("update_task", project_id=1, code=code, checked=True, expected_sha256=digest)
        self.assertFalse(updated.get("isError"), updated)
        self.assertEqual(self.tool("list_tasks", project_id=1, status="pending")["structuredContent"]["total"], 0)
        completed = self.tool("list_tasks", project_id=1, status="completed")["structuredContent"]
        self.assertEqual(completed["items"][0]["title"], "Implement login")
        reopened = self.tool("update_task", project_id=1, code=code, checked=False, expected_sha256=completed["sha256"])
        self.assertFalse(reopened.get("isError"), reopened)
        with self.sessions() as db:
            self.assertEqual(db.query(FileSnapshot).count(), 3)
        self.assertEqual(self.audit.page(tool="update_task", outcome="success")["total"], 2)
        self.assertNotIn("Implement login", str(self.audit.page()))

    def test_tasks_permissions_validation_and_preservation(self):
        path = self.workspace / ".documents/task/task.md"
        path.parent.mkdir(parents=True)
        original = "# Tasks\n\n- [ ] TASK-REQ-01-001: - First\n- [x] TASK-QA-ABC-001: - Second\n"
        path.write_text(original, encoding="utf-8")
        page = self.tool("list_tasks", project_id=1, limit=1)["structuredContent"]
        self.assertEqual(page["next_offset"], 1)
        self.assertEqual(self.tool("list_tasks", project_id=1, offset=1)["structuredContent"]["items"][0]["code"], "TASK-QA-ABC-001")
        args = dict(project_id=1, code="TASK-REQ-01-001", checked=True, expected_sha256=page["sha256"])
        self.grant = SimpleNamespace(project_ids=[1], can_write=False)
        self.assertTrue(self.tool("update_task", **args)["isError"])
        self.assertTrue(self.tool("create_task", project_id=1, code="TASK-REQ-01-002", title="Third", expected_sha256=page["sha256"])["isError"])
        self.grant = SimpleNamespace(project_ids=[], can_write=True)
        for tool in ("list_tasks", "list_requirements"):
            self.assertTrue(self.tool(tool, project_id=1)["isError"])
        self.assertTrue(self.tool("read_requirement", project_id=1, filepath=".documents/requirements/REQ-01.md")["isError"])
        self.grant = True
        for code, title in (("invalid", "Title"), ("TASK-REQ-01-002", "Injected\n- [x] item")):
            self.assertTrue(self.tool("create_task", project_id=1, code=code, title=title, expected_sha256=page["sha256"])["isError"])
        self.assertEqual(path.read_text(), original)
        self.assertFalse(self.tool("update_task", **args).get("isError"))
        self.assertEqual(path.read_text(), original.replace("[ ]", "[x]", 1))
        path.write_text(original + "- [ ] TASK-REQ-01-001: - Duplicate\n")
        args["expected_sha256"] = self.tool("list_tasks", project_id=1)["structuredContent"]["sha256"]
        self.assertTrue(self.tool("update_task", **args)["isError"])
        (self.workspace / ".gitideignore").write_text(".documents/task/task.md\n")
        self.assertTrue(self.tool("list_tasks", project_id=1)["isError"])
        self.assertTrue(self.tool("update_task", **args)["isError"])

    def test_requirement_discovery_read_and_exclusions(self):
        for directory in ("requirements", "functional-requirements", "spec", "specs"):
            folder = self.workspace / ".documents" / directory
            folder.mkdir(parents=True)
            (folder / "REQ-01.md").write_bytes(b"# Requirement\nAcceptance\n")
        (self.workspace / ".gitideignore").write_text(".documents/specs/*\n")
        page = self.tool("list_requirements", project_id=1, limit=2)["structuredContent"]
        self.assertEqual(page["total"], 3)
        self.assertEqual(page["next_offset"], 2)
        read = self.tool("read_requirement", project_id=1, filepath=page["items"][0]["path"], limit=1)["structuredContent"]
        self.assertEqual(read["content"], "# Requirement\n")
        self.assertEqual(read["next_line"], 2)
        for path in ("hello.txt", ".documents/requirements/../../hello.txt", ".documents/specs/REQ-01.md"):
            self.assertTrue(self.tool("read_requirement", project_id=1, filepath=path)["isError"])

    def test_search_pagination_and_exclusions(self):
        (self.workspace / "hello.txt").write_bytes(b"Needle\nneedle\nother\n")
        (self.workspace / "secret.txt").write_text("needle")
        (self.workspace / ".gitideignore").write_text("secret.txt")
        (self.workspace / "binary.dat").write_bytes(b"needle\x00")
        first = self.tool("search_files", project_id=1, query="needle", limit=1)["structuredContent"]
        self.assertEqual(first["items"][0]["line"], 1)
        second = self.tool("search_files", project_id=1, query="needle", offset=first["next_offset"], limit=1)["structuredContent"]
        self.assertEqual(second["items"][0]["line"], 2)
        self.assertIsNone(second["next_offset"])
        sensitive = self.tool("search_files", project_id=1, query="Needle", case_sensitive=True)["structuredContent"]
        self.assertEqual(len(sensitive["items"]), 1)

    def test_patch_conflicts_ambiguity_and_snapshot(self):
        (self.workspace / "hello.txt").write_bytes(b"same\nsame\n")
        digest = self.tool("read_file", project_id=1, filepath="hello.txt")["structuredContent"]["sha256"]
        args = dict(project_id=1, filepath="hello.txt", expected_sha256=digest,
                    target_content="same", replacement_content="new")
        self.assertTrue(self.tool("patch_file", **args)["isError"])
        result = self.tool("patch_file", **args, allow_multiple=True)["structuredContent"]
        self.assertEqual(result["replacements"], 2)
        self.assertEqual((self.workspace / "hello.txt").read_text(), "new\nnew\n")
        self.assertTrue(self.tool("patch_file", **args, allow_multiple=True)["isError"])
        with self.sessions() as db:
            self.assertEqual(db.query(FileSnapshot).count(), 1)
            self.assertEqual(db.query(ActivityLog).one().action_type, "FILE_PATCH")

    def test_git_diff_modes_and_ignored_file(self):
        from git import Repo, Actor
        repo = Repo.init(self.workspace)
        repo.index.add(["hello.txt"])
        actor = Actor("Test", "test@example.test")
        repo.index.commit("initial", author=actor, committer=actor)
        (self.workspace / "hello.txt").write_bytes(b"staged\n")
        repo.index.add(["hello.txt"])
        (self.workspace / "hello.txt").write_bytes(b"unstaged\n")
        unstaged = self.tool("git_diff", project_id=1, filepath="hello.txt")["structuredContent"]["diff"]
        staged = self.tool("git_diff", project_id=1, filepath="hello.txt", staged=True)["structuredContent"]["diff"]
        self.assertIn("+unstaged", unstaged)
        self.assertIn("+staged", staged)
        self.assertNotIn("+unstaged", staged)
        (self.workspace / ".gitideignore").write_text("hello.txt")
        self.assertTrue(self.tool("git_diff", project_id=1, filepath="hello.txt")["isError"])
        self.assertTrue(self.tool("git_diff", project_id=1, filepath="../secret")["isError"])
        repo.close()

    def test_read_write_conflict_and_snapshot(self):
        read = self.tool("read_file", project_id=1, filepath="hello.txt", limit=1)["structuredContent"]
        self.assertEqual(read["content"], "first\n")
        self.assertEqual(read["next_line"], 2)
        result = self.tool("write_file", project_id=1, filepath="hello.txt",
                           content="changed", expected_sha256=read["sha256"])
        self.assertFalse(result.get("isError", False))
        conflict = self.tool("write_file", project_id=1, filepath="hello.txt",
                             content="lost update", expected_sha256=read["sha256"])
        self.assertTrue(conflict["isError"])
        self.assertEqual((self.workspace / "hello.txt").read_text(), "changed")
        with self.sessions() as db:
            self.assertEqual(db.query(FileSnapshot).count(), 1)
            self.assertEqual(db.query(ActivityLog).count(), 1)

    def test_create_pagination_and_safety(self):
        created = self.tool("write_file", project_id=1, filepath="new.txt",
                            content="new", expected_sha256="missing")
        self.assertFalse(created.get("isError", False))
        page = self.tool("list_files", project_id=1, limit=1)["structuredContent"]
        self.assertEqual(page["next_offset"], 1)
        self.assertTrue(self.tool("read_file", project_id=999, filepath="hello.txt")["isError"])
        for path in ("../workspace-other/secret", "../secret", "C:/secret", ".git/config"):
            self.assertTrue(self.tool("write_file", project_id=1, filepath=path,
                                     content="bad", expected_sha256="missing")["isError"])
        (self.workspace / ".gitideignore").write_text("hello.txt\n", encoding="utf-8")
        self.assertTrue(self.tool("read_file", project_id=1, filepath="hello.txt")["isError"])
        self.assertTrue(self.tool("list_files", project_id=1, limit=201)["isError"])


if __name__ == "__main__":
    unittest.main()
