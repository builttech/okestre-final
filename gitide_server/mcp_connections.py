"""Connection metadata and persistent revocation independent of token rotation."""
import json
import time


class Connections:
    def __init__(self, store):
        self.store = store
        with store.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS mcp_connections (
                id TEXT PRIMARY KEY, metadata TEXT NOT NULL, authorized_at REAL,
                expires_at REAL NOT NULL, last_used_at REAL, revoked_at REAL)""")

    def ensure(self, family, source, name, authorized_at=None):
        identifier = self.store.key(family)
        metadata = json.dumps({"client_name": name, "client_id": source["client_id"],
            "subject": source.get("subject"), "project_ids": source.get("project_ids"),
            "can_write": source.get("can_write", True), "can_execute": source.get("can_execute", False)})
        with self.store.connect() as db:
            db.execute("""INSERT OR IGNORE INTO mcp_connections
                (id,metadata,authorized_at,expires_at) VALUES (?,?,?,?)""",
                (identifier, metadata, authorized_at, source["expires_at"]))
        return identifier

    def allowed(self, identifier):
        with self.store.connect() as db:
            row = db.execute("SELECT revoked_at,expires_at FROM mcp_connections WHERE id=?", (identifier,)).fetchone()
        return bool(row and row[0] is None and row[1] > time.time())

    def extend(self, identifier, expires):
        with self.store.connect() as db:
            db.execute("UPDATE mcp_connections SET expires_at=? WHERE id=? AND revoked_at IS NULL", (expires, identifier))

    def touch(self, identifier):
        now = time.time()
        with self.store.connect() as db:
            db.execute("""UPDATE mcp_connections SET last_used_at=? WHERE id=? AND revoked_at IS NULL
                AND (last_used_at IS NULL OR last_used_at < ?)""", (now, identifier, now - 60))

    def revoke(self, identifier):
        with self.store.connect() as db:
            cursor = db.execute("UPDATE mcp_connections SET revoked_at=COALESCE(revoked_at,?) WHERE id=?",
                                (time.time(), identifier))
            return bool(cursor.rowcount)

    def page(self, offset, limit, identifier=None):
        where = " WHERE id=?" if identifier else ""
        args = [identifier] if identifier else []
        with self.store.connect() as db:
            total = db.execute("SELECT COUNT(*) FROM mcp_connections" + where, args).fetchone()[0]
            rows = db.execute("""SELECT id,metadata,authorized_at,expires_at,last_used_at,revoked_at
                FROM mcp_connections""" + where + " ORDER BY COALESCE(authorized_at,0) DESC,id LIMIT ? OFFSET ?",
                args + [limit, offset]).fetchall()
        items = []
        for identifier, metadata, authorized, expires, used, revoked in rows:
            items.append(dict(json.loads(metadata), id=identifier, authorized_at=authorized,
                expires_at=expires, last_used_at=used, revoked_at=revoked,
                status="revoked" if revoked is not None else "expired" if expires <= time.time() else "active"))
        return {"items": items, "total": total, "next_offset": offset + limit if offset + limit < total else None}
