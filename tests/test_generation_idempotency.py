from fastapi.testclient import TestClient
import api.main as main
from api.workspace import WorkspaceRepository
from api.idempotency import GenerationReservation


def test_claim_once_and_replay(tmp_path):
    repo = WorkspaceRepository(tmp_path / "test.db")
    reservation = GenerationReservation(repo)
    assert reservation.claim("task", "request-key-0001")[0] == "CLAIMED"
    assert reservation.claim("task", "request-key-0001")[0] == "RUNNING"
    reservation.complete("task", "request-key-0001", "item-1")
    assert reservation.claim("task", "request-key-0001") == ("COMPLETE", "item-1")
    reservation.fail("task", "request-key-0001")
    assert reservation.claim("task", "request-key-0001")[0] == "COMPLETE"


def test_api_replays_same_draft_instead_of_generating_twice(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "workspace", WorkspaceRepository(tmp_path / "api.db"))
    client = TestClient(main.app)
    project = client.post("/api/projects", json={"name": "Demo"}).json()
    task = client.post("/api/tasks", json={"project_id": project["id"], "mode": "generate", "brief": "Disclosed product introduction", "quantity": 2}).json()
    path = f"/api/tasks/{task['id']}/generate-one"
    payload = {"request_key": "retry-same-key-001", "auto_review": False}
    first = client.post(path, json=payload)
    assert first.status_code == 200, first.text
    second = client.post(path, json=payload)
    assert second.status_code == 200, second.text
    assert first.json()["id"] == second.json()["id"]
    assert len(main.workspace.list_items(task["id"])) == 1
