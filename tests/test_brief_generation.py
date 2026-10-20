import pytest
from api.drafting import DraftGenerationService
from api.workspace import WorkspaceRepository, ProjectCreate, TaskCreate
from backend.providers import MockLLMProvider


def test_generate_one_saves_draft_with_human_review_pending(tmp_path):
    db = WorkspaceRepository(tmp_path/"drafts.sqlite3")
    project = db.create_project(ProjectCreate(name="Campaign", brand="Brand A", platform="小红书"))
    task = db.create_task(TaskCreate(project_id=project["id"], mode="generate", brief="公开透明的品牌产品介绍", quantity=2))
    item = DraftGenerationService(db, MockLLMProvider()).generate_one(task["id"])
    assert item["generation"]["mode"] == "demo"
    assert item["status"] == "DRAFT"
    assert item["current_version"] == 1
    assert WorkspaceRepository(tmp_path/"drafts.sqlite3").get_item(item["id"])["body"]
    assert len(db.list_versions(item["id"])) == 1


def test_generation_requires_mode_and_brief(tmp_path):
    db = WorkspaceRepository(tmp_path/"drafts.sqlite3")
    project = db.create_project(ProjectCreate(name="Campaign"))
    task = db.create_task(TaskCreate(project_id=project["id"], mode="review", brief="text"))
    with pytest.raises(ValueError, match="generate-mode"):
        DraftGenerationService(db, MockLLMProvider()).generate_one(task["id"])
    task = db.create_task(TaskCreate(project_id=project["id"], mode="generate"))
    with pytest.raises(ValueError, match="Brief"):
        DraftGenerationService(db, MockLLMProvider()).generate_one(task["id"])


def test_provider_failure_creates_no_item(tmp_path):
    db = WorkspaceRepository(tmp_path/"drafts.sqlite3")
    project = db.create_project(ProjectCreate(name="Campaign"))
    task = db.create_task(TaskCreate(project_id=project["id"], mode="generate", brief="brand post"))
    class Broken(MockLLMProvider):
        def generate(self, prompt, **kwargs):
            raise RuntimeError("provider down")
    with pytest.raises(RuntimeError):
        DraftGenerationService(db, Broken()).generate_one(task["id"])
    assert db.list_items(task["id"]) == []
