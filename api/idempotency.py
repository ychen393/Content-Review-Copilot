"""Durable per-task generation request reservations.

A retry of the same request key returns the same persisted item.
RUNNING/FAILED requests never silently trigger another billed model call.
"""
from __future__ import annotations
import json
from .workspace import WorkspaceRepository, timestamp
from .database import postgres_enabled


class GenerationReservation:
    def __init__(self, workspace: WorkspaceRepository):
        self.workspace = workspace
        with workspace.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS generation_requests (
                task_id TEXT NOT NULL, request_key TEXT NOT NULL,
                status TEXT NOT NULL, item_id TEXT, created_at TEXT NOT NULL,
                PRIMARY KEY(task_id, request_key)
            )""")

    def claim(self, task_id: str, key: str) -> tuple[str, str | None]:
        with self.workspace.connect() as db:
            # Serialize reservations for a task across serverless instances.
            if postgres_enabled():
                row = db.execute("SELECT payload FROM content_tasks WHERE id=? FOR UPDATE", (task_id,)).fetchone()
            else:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT payload FROM content_tasks WHERE id=?", (task_id,)).fetchone()
            if not row:
                raise LookupError("Task not found")
            task = json.loads(row[0])
            previous = db.execute("SELECT status, item_id FROM generation_requests WHERE task_id=? AND request_key=?", (task_id, key)).fetchone()
            if previous:
                return (previous[0], previous[1])
            count = db.execute("SELECT COUNT(*) FROM content_items WHERE task_id=?", (task_id,)).fetchone()[0]
            running = db.execute("SELECT COUNT(*) FROM generation_requests WHERE task_id=? AND status='RUNNING'", (task_id,)).fetchone()[0]
            if count + running >= task["quantity"]:
                return ("CAPACITY", None)
            db.execute("INSERT INTO generation_requests (task_id, request_key, status, created_at) VALUES (?, ?, 'RUNNING', ?)", (task_id, key, timestamp()))
            return ("CLAIMED", None)

    def complete(self, task_id: str, key: str, item_id: str):
        with self.workspace.connect() as db:
            db.execute("UPDATE generation_requests SET status='COMPLETE', item_id=? WHERE task_id=? AND request_key=? AND status='RUNNING'", (item_id, task_id, key))

    def fail(self, task_id: str, key: str):
        with self.workspace.connect() as db:
            db.execute("UPDATE generation_requests SET status='FAILED' WHERE task_id=? AND request_key=? AND status='RUNNING'", (task_id, key))
