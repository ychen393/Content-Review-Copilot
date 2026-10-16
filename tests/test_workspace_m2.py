from fastapi.testclient import TestClient
from api.main import app
import api.main as api_main
from api.workspace import WorkspaceRepository, ProjectCreate, TaskCreate, ItemCreate, VersionCreate
import pytest


def test_workspace_persistence_and_version_history(tmp_path):
    db = tmp_path / "workspace.sqlite3"
    store = WorkspaceRepository(db)
    project = store.create_project(ProjectCreate(name="Campaign", brand="Brand A", platform="xiaohongshu"))
    task = store.create_task(TaskCreate(project_id=project["id"], mode="review", quantity=2))
    item = store.create_item(task["id"], ItemCreate(title="Original", body="First draft", source_row=7))
    assert item["source_row"] == 7
    assert item["current_version"] == 1
    store.add_version(item["id"], VersionCreate(text="Second draft", title="Revised", created_by="user"))
    fresh = WorkspaceRepository(db)
    assert fresh.get_item(item["id"])["body"] == "Second draft"
    assert fresh.get_item(item["id"])["current_version"] == 2
    versions = fresh.list_versions(item["id"])
    assert [v["text"] for v in versions] == ["First draft", "Second draft"]
    assert [v["version_number"] for v in versions] == [1, 2]
    assert len(fresh.list_items(task["id"])) == 1


def test_task_limits_and_foreign_keys(tmp_path):
    store = WorkspaceRepository(tmp_path / "workspace.sqlite3")
    with pytest.raises(LookupError):
        store.create_task(TaskCreate(project_id="nonexistent", mode="generate"))
    project = store.create_project(ProjectCreate(name="Test"))
    task = store.create_task(TaskCreate(project_id=project["id"], mode="generate", quantity=1))
    store.create_item(task["id"], ItemCreate())
    with pytest.raises(ValueError):
        store.create_item(task["id"], ItemCreate())
    with pytest.raises(LookupError):
        store.add_version("missing", VersionCreate(text="nope"))


def test_workspace_api_and_legacy_health(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "workspace", WorkspaceRepository(tmp_path / "api.sqlite3"))
    client = TestClient(app)
    assert client.get("/api/health").status_code == 200
    project = client.post("/api/projects", json={"name": "Campaign"}).json()
    task_response = client.post("/api/tasks", json={"project_id": project["id"], "mode": "review", "quantity": 1})
    assert task_response.status_code == 200
    task = task_response.json()
    item = client.post(f"/api/tasks/{task['id']}/items", json={"title": "Draft", "body": "Content"}).json()
    assert item["current_version"] == 1
    assert client.get(f"/api/items/{item['id']}/versions").json()[0]["text"] == "Content"
    assert client.get(f"/api/projects/{project['id']}/tasks").json()[0]["id"] == task["id"]
    assert client.get("/api/projects/missing").status_code == 404
    assert client.post("/api/projects", json={"name": ""}).status_code == 422
