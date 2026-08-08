"""Real-DB smoke tests for task tools (list_tasks, create_task).

list_meetings / create_meeting already have real-DB coverage via the calendar
integration tests, so they are intentionally skipped here.
"""
import sys
import uuid

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text


def _teardown(db, org):
    for statement in [
        "DELETE FROM tasks WHERE organization_id = :id",
        "DELETE FROM meetings WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _org(db):
    from app.models.organization import Organization

    org = Organization(name="Task Org", slug=f"task-{uuid.uuid4().hex[:10]}", settings={})
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.mark.db
def test_list_tasks_handler_returns_real_row(db):
    from app.ai.tools.task_tools import TASK_TOOLS
    from app.models.task import Task

    org = _org(db)
    task = Task(
        organization_id=org.id,
        title="Fix login bug",
        description="The login endpoint 500s",
        priority="high",
        status="in_progress",
        ai_created=True,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        result = TASK_TOOLS["list_tasks"].handler(db, org.id, None, {})
        assert any(t["id"] == str(task.id) for t in result)
        row = next(t for t in result if t["id"] == str(task.id))
        assert row["title"] == "Fix login bug"
        assert row["priority"] == "high"
        assert row["status"] == "in_progress"
        assert row["ai_created"] is True

        filtered = TASK_TOOLS["list_tasks"].handler(
            db, org.id, None, {"status": "done"}
        )
        assert all(t["id"] != str(task.id) for t in filtered)
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_create_task_handler_persists_real_row(db):
    from app.ai.tools.task_tools import TASK_TOOLS
    from app.models.task import Task

    org = _org(db)

    try:
        result = TASK_TOOLS["create_task"].handler(
            db,
            org.id,
            None,
            {"title": "Send follow-up", "priority": "medium", "status": "todo"},
        )
        assert result.get("ai_created") is True
        assert result.get("title") == "Send follow-up"

        task = db.query(Task).filter(Task.organization_id == org.id).first()
        assert task is not None
        assert task.title == "Send follow-up"
        assert task.priority == "medium"
        assert task.status == "todo"
        assert task.ai_created is True
    finally:
        _teardown(db, org)