from fastapi.testclient import TestClient
import api.main as main
from api.workspace import WorkspaceRepository


def test_item_review_lifecycle_links_versions_and_decisions(tmp_path, monkeypatch):
    from api.service import ReviewWorkflowService
    from api.store import ReviewStore
    repo = WorkspaceRepository(tmp_path / "workspace.sqlite3")
    service = ReviewWorkflowService(store=ReviewStore(tmp_path / "reviews.sqlite3"))
    monkeypatch.setattr(main, "workspace", repo)
    monkeypatch.setattr(main, "service", service)
    client = TestClient(main.app)
    project = client.post("/api/projects", json={"name": "Campaign", "brand": "Brand X"}).json()
    task = client.post("/api/tasks", json={"project_id": project["id"], "mode": "review", "quantity": 1}).json()
    item = client.post(f"/api/tasks/{task['id']}/items", json={"title": "A", "body": "我分享这个产品的使用过程。"}).json()
    url = f"/api/items/{item['id']}/review"
    first = client.post(url)
    assert first.status_code == 200, first.text
    session = first.json()
    assert client.post(url).json()["id"] == session["id"]
    assert repo.get_item(item["id"])["review_session_id"] == session["id"]
    reviewed = client.post(f"/api/reviews/{session['id']}/first-review")
    assert reviewed.status_code == 200, reviewed.text
    saved = WorkspaceRepository(tmp_path / "workspace.sqlite3").get_item(item["id"])
    assert saved["review_state"] == reviewed.json()["state"]
    assert saved["current_version"] == 1
    assert saved["review_decisions"] == {"first": {}, "second": {}}
    assert client.get(f"/api/items/{item['id']}/versions").status_code == 200


def test_review_requires_nonempty_item(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "workspace", WorkspaceRepository(tmp_path / "workspace.sqlite3"))
    client = TestClient(main.app)
    p = client.post("/api/projects", json={"name": "Example"}).json()
    task = client.post("/api/tasks", json={"project_id": p["id"], "mode": "review"}).json()
    item = client.post(f"/api/tasks/{task['id']}/items", json={}).json()
    assert client.post(f"/api/items/{item['id']}/review").status_code == 409
