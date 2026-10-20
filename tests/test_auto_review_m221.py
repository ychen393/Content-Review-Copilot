from api.drafting import DraftGenerationService
from api.workspace import WorkspaceRepository, ProjectCreate, TaskCreate
from api.service import ReviewWorkflowService
from api.store import ReviewStore
from backend.providers import MockLLMProvider


def test_auto_review_creates_session_and_persists_provenance(tmp_path):
    workspace = WorkspaceRepository(tmp_path / "workspace.db")
    service = ReviewWorkflowService(store=ReviewStore(tmp_path / "review.db"), provider=MockLLMProvider())
    project = workspace.create_project(ProjectCreate(name="Campaign", brand="Brand X"))
    task = workspace.create_task(TaskCreate(project_id=project["id"], mode="generate", brief="Clear disclosed marketing copy"))
    item = DraftGenerationService(workspace, MockLLMProvider()).generate_one(task["id"], auto_review=True, review_service=service)
    assert item["generation"]["mode"] == "demo"
    assert item["review_session_id"]
    saved = ReviewStore(tmp_path / "review.db").get(item["review_session_id"])
    assert saved["firstReview"] is not None
    assert saved["state"] in ("FIRST_REVIEW_COMPLETE", "WAITING_FOR_FIRST_DECISIONS")
    assert workspace.get_item(item["id"])["current_version"] == 1


def test_auto_review_failure_retains_original_draft(tmp_path):
    workspace = WorkspaceRepository(tmp_path / "workspace.db")
    project = workspace.create_project(ProjectCreate(name="Campaign"))
    task = workspace.create_task(TaskCreate(project_id=project["id"], mode="generate", brief="Disclosed brand message"))
    class FailingReviewer:
        def create(self, request):
            raise RuntimeError("review provider down")
    item = DraftGenerationService(workspace, MockLLMProvider()).generate_one(task["id"], auto_review=True, review_service=FailingReviewer())
    assert item["status"] == "REVIEW_FAILED"
    assert item["current_version"] == 1
    assert workspace.list_versions(item["id"])[0]["text"] == item["body"]
