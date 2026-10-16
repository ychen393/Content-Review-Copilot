"""Database adapter contract tests, no real Neon credential required."""
from unittest.mock import patch
import sqlite3
import pytest
from api.database import connect, postgres_enabled, PostgresConnection
from api.workspace import WorkspaceRepository, ProjectCreate, TaskCreate, ItemCreate


def test_sqlite_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "local.db"
    repo = WorkspaceRepository(db)
    p = repo.create_project(ProjectCreate(name="Demo"))
    task = repo.create_task(TaskCreate(project_id=p["id"], mode="review"))
    item = repo.create_item(task["id"], ItemCreate(body="Draft"))
    assert WorkspaceRepository(db).get_item(item["id"])["body"] == "Draft"
    assert not postgres_enabled()


def test_connection_adapter_rewrites_parameters(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/db")
    calls = []
    class FakeConnection:
        def execute(self, query, args=()):
            calls.append((query, args))
            return self
        def commit(self): calls.append(("COMMIT", ()))
        def close(self): calls.append(("CLOSE", ()))
        def rollback(self): calls.append(("ROLLBACK", ()))
    with patch("psycopg.connect", return_value=FakeConnection()) as mocked:
        with connect("should-not-write.sqlite3") as db:
            db.execute("SELECT payload FROM projects WHERE id=?", ("id1",))
            db.execute("BEGIN IMMEDIATE")
            db.executescript("PRAGMA foreign_keys=ON; CREATE TABLE IF NOT EXISTS sample (id TEXT PRIMARY KEY);")
    mocked.assert_called_once()
    assert calls[0] == ("SELECT payload FROM projects WHERE id=%s", ("id1",))
    assert any("CREATE TABLE" in q for q, _ in calls)
    assert all("PRAGMA" not in q for q, _ in calls)
    assert ("COMMIT", ()) in calls
