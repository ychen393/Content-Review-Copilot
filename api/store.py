from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from .database import connect as database_connect


class ReviewStore:
    def __init__(self, path: str | Path = "data/history.sqlite3") -> None:
        self.path = str(path)
        with database_connect(self.path) as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS review_workflows (
                session_id TEXT PRIMARY KEY, created_time TEXT NOT NULL,
                updated_time TEXT NOT NULL, payload TEXT NOT NULL)""")

    def save(self, session_id: str, created: str, updated: str, payload: dict) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT INTO review_workflows VALUES (?, ?, ?, ?) ON CONFLICT(session_id) DO UPDATE SET updated_time=excluded.updated_time, payload=excluded.payload",
                (session_id, created, updated, json.dumps(payload, ensure_ascii=False)),
            )

    def get(self, session_id: str) -> dict | None:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute("SELECT payload FROM review_workflows WHERE session_id=?", (session_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def list(self) -> list[dict]:
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute("SELECT payload FROM review_workflows ORDER BY updated_time DESC").fetchall()
        return [json.loads(row[0]) for row in rows]

