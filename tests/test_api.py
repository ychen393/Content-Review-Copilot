from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app, service
from api.store import ReviewStore
from api.service import evidence_issues, unsupported_claims


def client(tmp_path: Path) -> TestClient:
    service.store = ReviewStore(tmp_path / "history.sqlite3")
    return TestClient(app)


def create_review(test_client: TestClient, text: str = "这是示例品牌的产品体验。") -> dict:
    response = test_client.post("/api/reviews", json={"original_text": text, "keyword": "示例品牌"})
    assert response.status_code == 200
    return response.json()


def test_session_creation_freezes_policy(tmp_path):
    review = create_review(client(tmp_path))
    assert review["state"] == "NEW_REVIEW"
    assert len(review["reviewBasis"]) == 6


def test_document_parse_endpoint(tmp_path):
    response = client(tmp_path).post("/api/documents/parse", files={"file": ("draft.md", "# 标题\n正文".encode("utf-8"), "text/markdown")})
    assert response.status_code == 200
    assert response.json()["filename"] == "draft.md"


def test_first_review_and_history(tmp_path):
    test_client = client(tmp_path); review = create_review(test_client)
    first = test_client.post(f"/api/reviews/{review['id']}/first-review")
    assert first.status_code == 200
    assert first.json()["state"] in {"FIRST_REVIEW_COMPLETE", "WAITING_FOR_FIRST_DECISIONS"}
    assert test_client.get("/api/reviews").json()[0]["id"] == review["id"]


def test_financial_evidence_regression():
    text = "本产品保证年化收益率不低于8%，超过90%的用户表示满意。"
    issues = evidence_issues(text)
    assert any(item["id"] == "evidence_guaranteed_return" for item in issues)
    assert any(item["id"].startswith("evidence_stat") for item in issues)
    assert unsupported_claims(text, text + " 根据2024年调查（N=3,200）获得创新奖")


def test_mandatory_issue_cannot_silently_pass(tmp_path):
    test_client = client(tmp_path)
    review = create_review(test_client, "本产品保证年化收益率不低于8%，投资者可放心购买。")
    first = test_client.post(f"/api/reviews/{review['id']}/first-review").json()
    mandatory = next(item for item in first["firstReview"] if item["isMandatory"])
    response = test_client.post(f"/api/reviews/{review['id']}/rewrite")
    assert response.status_code == 409
    accepted = test_client.post(f"/api/reviews/{review['id']}/decisions", json={"stage": "first", "decisions": {mandatory["id"]: "accepted"}})
    assert accepted.status_code == 200
