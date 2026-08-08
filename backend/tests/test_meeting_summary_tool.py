"""summarize_meeting tool tests (model_router.complete mocked; no LLM calls)."""
import json
import sys
import uuid

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text

from app.ai.tools.task_tools import TASK_TOOLS, _NOTES_LIMIT


def _org(db):
    from app.models.organization import Organization

    org = Organization(
        name="Meeting Test Org",
        slug=f"meeting-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _teardown(db, org):
    deletes = [
        "DELETE FROM meetings WHERE organization_id = :id",
        "DELETE FROM storage_quotas WHERE organization_id = :id",
        "DELETE FROM reminders WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM ai_employees WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _meeting(db, org, title="Team sync"):
    from app.models.meeting import Meeting

    meeting = Meeting(organization_id=org.id, title=title, participants=[])
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def _fresh_meeting(db, meeting_id):
    from app.models.meeting import Meeting

    return db.get(Meeting, meeting_id)


def test_summarize_meeting_persists_rows(db, monkeypatch):
    monkeypatch.setattr(
        "app.ai.tools.task_tools.model_router.complete",
        lambda messages, temperature=0.3: json.dumps(
            {
                "summary": "We agreed on the Q3 roadmap and staffing plan.",
                "action_items": [
                    {"item": "Draft roadmap doc", "owner": "alice", "due_hint": "Friday"},
                    {"item": "Confirm headcount", "owner": "bob", "due_hint": "next week"},
                ],
                "key_decisions": ["Q3 focus on platform reliability"],
            }
        ),
    )

    org = _org(db)
    m = _meeting(db, org)
    notes = "Discussed roadmap. Alice owns drafting. Bob owns headcount."

    try:
        result = TASK_TOOLS["summarize_meeting"].handler(
            db, org.id, None, {"meeting_id": str(m.id), "notes": notes}
        )
        assert result["source"] == "llm"
        assert result["meeting_id"] == str(m.id)
        assert result["summary"] == "We agreed on the Q3 roadmap and staffing plan."
        assert len(result["action_items"]) == 2
        assert result["action_items"][0]["owner"] == "alice"
        assert result["action_items"][0]["due_hint"] == "Friday"
        assert result["key_decisions"] == ["Q3 focus on platform reliability"]

        # persist check: re-read the row fresh from the DB
        fresh = _fresh_meeting(db, m.id)
        assert fresh.transcript == notes
        assert fresh.summary == "We agreed on the Q3 roadmap and staffing plan."
        assert fresh.action_items == result["action_items"]
    finally:
        _teardown(db, org)


def test_summarize_meeting_not_found(db, monkeypatch):
    called = {"n": 0}

    def boom(messages, temperature=0.3):
        called["n"] += 1
        raise AssertionError("should not be called")

    monkeypatch.setattr("app.ai.tools.task_tools.model_router.complete", boom)

    org = _org(db)
    try:
        result = TASK_TOOLS["summarize_meeting"].handler(
            db, org.id, None, {"meeting_id": str(uuid.uuid4()), "notes": "Some notes"}
        )
        assert result == {"error": "Meeting not found"}
        assert called["n"] == 0
    finally:
        _teardown(db, org)


def test_summarize_meeting_model_error_falls_back(db, monkeypatch):
    def boom(messages, temperature=0.3):
        raise RuntimeError("rate limit exceeded")

    monkeypatch.setattr("app.ai.tools.task_tools.model_router.complete", boom)

    org = _org(db)
    m = _meeting(db, org)
    notes = "Discussed hiring plan. Vendor review next. Budget is approved."

    try:
        result = TASK_TOOLS["summarize_meeting"].handler(
            db, org.id, None, {"meeting_id": str(m.id), "notes": notes}
        )
        assert "error" not in result
        assert result["source"] == "data"
        assert result["action_items"] == []
        assert isinstance(result["summary"], str) and result["summary"]
        # fallback summary still persisted
        fresh = _fresh_meeting(db, m.id)
        assert fresh.summary == result["summary"]
    finally:
        _teardown(db, org)


def test_summarize_meeting_truncates_long_notes(db, monkeypatch):
    captured = {}

    def fake(messages, temperature=0.3):
        captured["notes"] = messages[1]["content"]
        return json.dumps({"summary": "ok", "action_items": [], "key_decisions": []})

    monkeypatch.setattr("app.ai.tools.task_tools.model_router.complete", fake)

    org = _org(db)
    m = _meeting(db, org)
    long_notes = "line about project status\n" * 500

    try:
        result = TASK_TOOLS["summarize_meeting"].handler(
            db, org.id, None, {"meeting_id": str(m.id), "notes": long_notes}
        )
        assert result["truncated"] is True
        assert len(captured["notes"]) <= _NOTES_LIMIT
    finally:
        _teardown(db, org)
