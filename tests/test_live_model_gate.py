from fastapi.testclient import TestClient
import api.main as main
from api.workspace import WorkspaceRepository


def test_vercel_requires_live_model_before_generation(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "workspace", WorkspaceRepository(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    client = TestClient(main.app)
    project = client.post("/api/projects", json={"name": "Test"}).json()
    task = client.post("/api/tasks", json={"project_id": project["id"], "mode": "generate", "brief": "Brand messaging"}).json()
    response = client.post(f"/api/tasks/{task['id']}/generate-one", json={"request_key": "live-config-test-0001", "auto_review": False})
    assert response.status_code == 409
    assert "真实模型尚未配置" in response.json()["detail"]
    assert main.workspace.list_items(task["id"]) == []
    assert client.get("/api/models/status").json()["mode"] == "demo"
