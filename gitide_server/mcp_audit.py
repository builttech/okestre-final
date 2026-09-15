"""Allowlisted MCP audit metadata. Never persist arguments, results or exceptions."""
import json
import time


class MCPAudit:
    def __init__(self, store):
        self.store = store
        with store.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS mcp_audit (
                id INTEGER PRIMARY KEY, occurred_at REAL NOT NULL, connection_id TEXT,
                auth_type TEXT NOT NULL, subject TEXT, tool TEXT, project_id INTEGER,
                outcome TEXT NOT NULL, duration_ms INTEGER NOT NULL)""")
            db.execute("CREATE INDEX IF NOT EXISTS mcp_audit_time ON mcp_audit(occurred_at DESC,id DESC)")
            db.execute("CREATE INDEX IF NOT EXISTS mcp_audit_connection ON mcp_audit(connection_id,id DESC)")

    def record(self, *, grant, tool, project_id, outcome, duration_ms):
        connection = getattr(grant, "connection_id", None)
        subject = getattr(grant, "subject", None)
        auth_type = "oauth" if grant and grant is not True else "api_key" if grant is True else "unauthenticated"
        with self.store.connect() as db:
            db.execute("""INSERT INTO mcp_audit
                (occurred_at,connection_id,auth_type,subject,tool,project_id,outcome,duration_ms)
                VALUES (?,?,?,?,?,?,?,?)""", (time.time(), connection, auth_type, subject,
                tool, project_id, outcome, max(0, int(duration_ms))))

    def page(self, *, offset=0, limit=50, connection_id=None, project_id=None,
             tool=None, outcome=None, start=None, end=None):
        clauses, args = [], []
        for column, value, operator in (("connection_id", connection_id, "="), ("project_id", project_id, "="),
                ("tool", tool, "="), ("outcome", outcome, "="), ("occurred_at", start, ">="), ("occurred_at", end, "<=")):
            if value is not None:
                clauses.append(f"a.{column} {operator} ?")
                args.append(value)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.store.connect() as db:
            total = db.execute("SELECT COUNT(*) FROM mcp_audit a" + where, args).fetchone()[0]
            rows = db.execute("""SELECT a.id,a.occurred_at,a.connection_id,a.auth_type,a.subject,
                a.tool,a.project_id,a.outcome,a.duration_ms,c.metadata
                FROM mcp_audit a LEFT JOIN mcp_connections c ON c.id=a.connection_id""" + where +
                " ORDER BY a.occurred_at DESC,a.id DESC LIMIT ? OFFSET ?", args + [limit, offset]).fetchall()
            options = db.execute("""SELECT DISTINCT a.connection_id,c.metadata FROM mcp_audit a
                JOIN mcp_connections c ON c.id=a.connection_id ORDER BY a.connection_id""").fetchall()
            tools = [row[0] for row in db.execute("SELECT DISTINCT tool FROM mcp_audit WHERE tool IS NOT NULL ORDER BY tool")]
            projects = [row[0] for row in db.execute("SELECT DISTINCT project_id FROM mcp_audit WHERE project_id IS NOT NULL ORDER BY project_id")]
        items = []
        for identifier, occurred, connection, auth, subject, tool_name, project, result, duration, metadata in rows:
            name = json.loads(metadata)["client_name"] if metadata else "Chave API global" if auth == "api_key" else "Nao identificado"
            items.append({"id": identifier, "occurred_at": occurred, "connection_id": connection,
                "application": name, "auth_type": auth, "subject": subject, "tool": tool_name,
                "project_id": project, "outcome": result, "duration_ms": duration})
        return {"items": items, "total": total, "next_offset": offset + limit if offset + limit < total else None,
                "connections": [{"id": identifier, "name": json.loads(metadata)["client_name"]} for identifier, metadata in options],
                "tools": tools, "project_ids": projects}
