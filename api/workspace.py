"""M2.1 persisted content workspace: projects, tasks, items and immutable versions."""
from __future__ import annotations
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    brand: str = ""
    product: str = ""
    platform: str = ""
    description: str = ""


class TaskCreate(BaseModel):
    project_id: str
    mode: Literal["generate", "review"]
    brief: str = ""
    quantity: int = Field(default=1, ge=1, le=20)


class ItemCreate(BaseModel):
    title: str = ""
    body: str = ""
    source_row: int | None = Field(default=None, ge=1)


class VersionCreate(BaseModel):
    text: str
    title: str = ""
    created_by: Literal["user", "ai", "system"] = "user"
    reason: str = ""


class WorkspaceRepository:
    def __init__(self, path: str | Path = "data/history.sqlite3"):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS content_tasks (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
                payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS content_items (
                id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES content_tasks(id),
                payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS content_versions (
                item_id TEXT NOT NULL REFERENCES content_items(id),
                version_number INTEGER NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY(item_id, version_number));
            CREATE INDEX IF NOT EXISTS idx_tasks_project ON content_tasks(project_id);
            CREATE INDEX IF NOT EXISTS idx_items_task ON content_items(task_id);
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def _insert(self, table, payload, **foreign):
        identifier = str(uuid.uuid4())
        created = timestamp()
        row = {"id": identifier, **foreign, **payload, "created_at": created}
        columns = ["id", *foreign, "payload", "created_at"]
        values = [identifier, *foreign.values(), json.dumps(row, ensure_ascii=False), created]
        with self.connect() as db:
            db.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in values)})", values)
        return row

    def _get(self, table, identifier):
        with self.connect() as db:
            result = db.execute(f"SELECT payload FROM {table} WHERE id=?", (identifier,)).fetchone()
        return json.loads(result[0]) if result else None

    def _list(self, table, foreign_key=None, foreign_id=None):
        with self.connect() as db:
            if foreign_key:
                rows = db.execute(f"SELECT payload FROM {table} WHERE {foreign_key}=? ORDER BY created_at, id", (foreign_id,)).fetchall()
            else:
                rows = db.execute(f"SELECT payload FROM {table} ORDER BY created_at, id").fetchall()
        return [json.loads(row[0]) for row in rows]

    def create_project(self, model: ProjectCreate):
        return self._insert("projects", model.model_dump())

    def list_projects(self):
        return self._list("projects")

    def get_project(self, project_id):
        return self._get("projects", project_id)

    def create_task(self, model: TaskCreate):
        if not self.get_project(model.project_id):
            raise LookupError("Project not found")
        return self._insert("content_tasks", {
            "mode": model.mode, "brief": model.brief, "quantity": model.quantity, "status": "CREATED",
        }, project_id=model.project_id)

    def get_task(self, task_id):
        return self._get("content_tasks", task_id)

    def list_tasks(self, project_id):
        if not self.get_project(project_id):
            raise LookupError("Project not found")
        return self._list("content_tasks", "project_id", project_id)

    def create_item(self, task_id: str, model: ItemCreate):
        task = self.get_task(task_id)
        if not task:
            raise LookupError("Task not found")
        with self.connect() as db:
            count = db.execute("SELECT COUNT(*) FROM content_items WHERE task_id=?", (task_id,)).fetchone()[0]
        if count >= task["quantity"]:
            raise ValueError("Task item limit reached")
        item = self._insert("content_items", {
            **model.model_dump(), "status": "DRAFT", "current_version": 0,
        }, task_id=task_id)
        if model.body:
            self.add_version(item["id"], VersionCreate(text=model.body, title=model.title, reason="Initial content"))
        return self.get_item(item["id"])

    def get_item(self, item_id):
        return self._get("content_items", item_id)

    def list_items(self, task_id):
        if not self.get_task(task_id):
            raise LookupError("Task not found")
        return self._list("content_items", "task_id", task_id)

    def add_version(self, item_id: str, model: VersionCreate):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT payload FROM content_items WHERE id=?", (item_id,)).fetchone()
            if not current:
                raise LookupError("Content item not found")
            item = json.loads(current[0])
            number = item["current_version"] + 1
            version = {"item_id": item_id, "version_number": number, **model.model_dump(), "created_at": timestamp()}
            db.execute("INSERT INTO content_versions VALUES (?,?,?)",
                       (item_id, number, json.dumps(version, ensure_ascii=False)))
            item.update(title=model.title or item["title"], body=model.text, current_version=number)
            db.execute("UPDATE content_items SET payload=? WHERE id=?",
                       (json.dumps(item, ensure_ascii=False), item_id))
        return version

    def list_versions(self, item_id):
        if not self.get_item(item_id):
            raise LookupError("Content item not found")
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM content_versions WHERE item_id=? ORDER BY version_number", (item_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]
