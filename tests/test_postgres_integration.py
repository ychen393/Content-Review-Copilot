"""PostgreSQL integration coverage; CI runs against a disposable PostgreSQL service."""
import os
import pytest
from api.workspace import WorkspaceRepository, ProjectCreate, TaskCreate, ItemCreate, VersionCreate
from api.store import ReviewStore

@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="Requires disposable PostgreSQL instance")
def test_postgres_persistence_across_connections(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_POSTGRES_URL"])
    first = WorkspaceRepository("ignored.sqlite3")
    project = first.create_project(ProjectCreate(name="Postgres E2E"))
    task = first.create_task(TaskCreate(project_id=project["id"], mode="review", quantity=1))
    item = first.create_item(task["id"], ItemCreate(title="Draft", body="Original copy"))
    assert item["current_version"] == 1
    second = WorkspaceRepository("ignored.sqlite3")
    assert second.get_project(project["id"])["name"] == "Postgres E2E"
    second.add_version(item["id"], VersionCreate(text="Updated copy", reason="human edit"))
    fresh = WorkspaceRepository("ignored.sqlite3")
    assert fresh.get_item(item["id"])["body"] == "Updated copy"
    assert [v["version_number"] for v in fresh.list_versions(item["id"])] == [1, 2]
    session = ReviewStore("ignored.sqlite3")
    session.save("test-postgres-review", "2026-10-20", "2026-10-20", {"state":"NEW_REVIEW"})
    assert ReviewStore("ignored.sqlite3").get("test-postgres-review")["state"] == "NEW_REVIEW"
    # The test database is disposable, but remove the test rows explicitly as well.
    with first.connect() as db:
        db.execute("DELETE FROM review_workflows WHERE session_id=?", ("test-postgres-review",))
        db.execute("DELETE FROM content_versions WHERE item_id=?", (item["id"],))
        db.execute("DELETE FROM content_items WHERE id=?", (item["id"],))
        db.execute("DELETE FROM content_tasks WHERE id=?", (task["id"],))
        db.execute("DELETE FROM projects WHERE id=?", (project["id"],))
