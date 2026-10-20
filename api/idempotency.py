"""Durable per-task generation request reservations.

A retry of the same request key returns the same persisted item.
RUNNING/FAILED requests never silently trigger another billed model call.
"""
from __future__ import annotations
import json
from .workspace import WorkspaceRepository, timestamp


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
            inserted = db.execute("INSERT INTO generation_requests (task_id, request_key, status, created_at) VALUES (?, ?, 'RUNNING', ?) ON CONFLICT(task_id, request_key) DO NOTHING RETURNING status", (task_id, key, timestamp())).fetchone()
            row = db.execute("SELECT status, item_id FROM generation_requests WHERE task_id=? AND request_key=?", (task_id, key)).fetchone()
            # The insert and read execute in the same transaction; concurrency-safe
            # uniqueness lives in the database, not process memory.
            return ("CLAIMED" if inserted else row[0], row[1])

    def complete(self, task_id: str, key: str, item_id: str):
        with self.workspace.connect() as db:
            db.execute("UPDATE generation_requests SET status='COMPLETE', item_id=? WHERE task_id=? AND request_key=? AND status='RUNNING'", (item_id, task_id, key))

    def fail(self, task_id: str, key: str):
        with self.workspace.connect() as db:
            db.execute("UPDATE generation_requests SET status='FAILED' WHERE task_id=? AND request_key=? AND status='RUNNING'", (task_id, key))
