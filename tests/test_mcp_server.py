import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gitide_server.database import Base, Project, FileSnapshot, ActivityLog
from gitide_server.mcp_server import create_mcp


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
        _, transport, lifespan = create_mcp(
            lambda req: req.headers.get("authorization") == "Bearer test-token", self.sessions)
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

    def test_auth_and_origin(self):
        for token in (None, "wrong"):
            self.assertEqual(self.rpc("tools/list", token=token).status_code, 401)
        self.assertEqual(self.rpc("tools/list", extra_headers={"Origin": "https://evil.example"}).status_code, 403)

    def test_initialize_and_discovery(self):
        response = self.rpc("initialize", {"protocolVersion": "2025-06-18",
            "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}})
        self.assertEqual(response.status_code, 200)
        self.assertIn("serverInfo", response.json()["result"])
        tools = self.rpc("tools/list").json()["result"]["tools"]
        self.assertEqual({t["name"] for t in tools},
                         {"list_projects", "list_files", "read_file", "write_file", "git_status"})

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
