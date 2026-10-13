from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .models import AnalysisSession, AnalysisVersion


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HistoryRepository:
    def __init__(self, path: str | Path = "data/history.sqlite3") -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, created_time TEXT, updated_time TEXT, metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS versions (session_id TEXT, version_number INTEGER, created_time TEXT, payload TEXT NOT NULL, PRIMARY KEY(session_id, version_number));
            """)

    def create_session(self, metadata: dict[str, Any]) -> str:
        session_id = str(uuid.uuid4())
        now = utc_now()
        with sqlite3.connect(self.path) as connection:
            connection.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", (session_id, now, now, json.dumps(metadata, ensure_ascii=False)))
        return session_id

    def save_version(self, session_id: str, payload: dict[str, Any]) -> AnalysisVersion:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute("SELECT COALESCE(MAX(version_number), 0) + 1 FROM versions WHERE session_id = ?", (session_id,)).fetchone()
            version_number = int(row[0])
            version = {**payload, "version_number": version_number, "created_time": utc_now()}
            connection.execute("INSERT INTO versions VALUES (?, ?, ?, ?)", (session_id, version_number, version["created_time"], json.dumps(version, ensure_ascii=False)))
            connection.execute("UPDATE sessions SET updated_time = ? WHERE session_id = ?", (version["created_time"], session_id))
        return AnalysisVersion.model_validate(version)

    def list_sessions(self) -> list[AnalysisSession]:
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute("SELECT session_id, created_time, updated_time, metadata FROM sessions ORDER BY updated_time DESC").fetchall()
        return [AnalysisSession(session_id=row[0], created_time=row[1], updated_time=row[2], **json.loads(row[3])) for row in rows]

    def get_versions(self, session_id: str) -> list[AnalysisVersion]:
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute("SELECT payload FROM versions WHERE session_id = ? ORDER BY version_number", (session_id,)).fetchall()
        return [AnalysisVersion.model_validate(json.loads(row[0])) for row in rows]
