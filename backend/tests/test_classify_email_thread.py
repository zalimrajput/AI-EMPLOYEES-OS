"""classify_email_thread tool tests (model_router.complete mocked; no LLM calls)."""
import json
import sys
import uuid

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text

from app.ai.tools.marketing_tools import MARKETING_TOOLS, _BODY_LIMIT, _EMAILS_CAP, _BODY_LIMIT, _EMAILS_CAP


def _org(db):
    from app.models.organization import Organization

    org = Organization(
        name="Classify Test Org",
        slug=f"classify-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _teardown(db, org):
    deletes = [
        "DELETE FROM emails WHERE organization_id = :id",
        "DELETE FROM email_threads WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _thread(db, org, subject="Urgent server down"):
    from app.models.email import Email, EmailThread

    thread = EmailThread(organization_id=org.id, subject=subject, participants={})
    db.add(thread)
    db.flush()
    email = Email(
        organization_id=org.id,
        thread_id=thread.id,
        body="Our website is down and it is losing us money right now!",
        direction="inbound",
    )
    db.add(email)
    db.commit()
    db.refresh(thread)
    return thread


def _fresh_thread(db, thread_id):
    from app.models.email import EmailThread

    return db.get(EmailThread, thread_id)


def test_classify_persists_priority_and_category(db, monkeypatch):
    monkeypatch.setattr(
        "app.ai.model_router.complete",
        lambda messages, temperature=0.3: json.dumps(
            {
                "priority": "urgent",
                "category": "support issue",
                "requires_response": True,
                "reasoning": "The website is down and causing revenue loss.",
            }
        ),
    )

    org = _org(db)
    thread = _thread(db, org)

    try:
        result = MARKETING_TOOLS["classify_email_thread"].handler(
            db, org.id, None, {"thread_id": str(thread.id)}
        )
        assert result["source"] == "llm"
        assert result["thread_id"] == str(thread.id)
        assert result["priority"] == "urgent"
        assert result["category"] == "support issue"
        assert result["requires_response"] is True

        fresh = _fresh_thread(db, thread.id)
        assert fresh.ai_priority == "urgent"
        assert fresh.category == "support issue"
    finally:
        _teardown(db, org)


def test_classify_email_thread_not_found(db, monkeypatch):
    called = {"n": 0}

    def boom(messages, temperature=0.3):
        called["n"] += 1
        raise AssertionError("should not be called")

    monkeypatch.setattr("app.ai.model_router.complete", boom)

    org = _org(db)
    try:
        result = MARKETING_TOOLS["classify_email_thread"].handler(
            db, org.id, None, {"thread_id": str(uuid.uuid4())}
        )
        assert result == {"error": "Email thread not found"}
        assert called["n"] == 0
    finally:
        _teardown(db, org)


def test_classify_email_thread_model_error_falls_back(db, monkeypatch):
    def boom(messages, temperature=0.3):
        raise RuntimeError("rate limit exceeded")

    monkeypatch.setattr("app.ai.model_router.complete", boom)

    org = _org(db)
    thread = _thread(db, org)

    try:
        result = MARKETING_TOOLS["classify_email_thread"].handler(
            db, org.id, None, {"thread_id": str(thread.id)}
        )
        assert "error" not in result
        assert result["source"] == "data"
        assert result["priority"] == "normal"
        assert result["category"] == "unclassified"
        assert result["requires_response"] is True

        fresh = _fresh_thread(db, thread.id)
        assert fresh.ai_priority == "normal"
        assert fresh.category == "unclassified"
    finally:
        _teardown(db, org)


def test_classify_email_thread_truncates_long_bodies(db, monkeypatch):
    captured = {}

    def fake(messages, temperature=0.3):
        captured["content"] = messages[1]["content"]
        return json.dumps(
            {
                "priority": "normal",
                "category": "spam",
                "requires_response": False,
                "reasoning": "looks like spam",
            }
        )

    monkeypatch.setattr("app.ai.model_router.complete", fake)

    from app.models.email import Email, EmailThread

    org = _org(db)
    thread = EmailThread(organization_id=org.id, subject="Promo", participants={})
    db.add(thread)
    db.flush()
    long_body = "offer details " * 500  # well over _BODY_LIMIT
    db.add(
        Email(
            organization_id=org.id,
            thread_id=thread.id,
            body=long_body,
            direction="inbound",
        )
    )
    db.commit()
    db.refresh(thread)

    try:
        result = MARKETING_TOOLS["classify_email_thread"].handler(
            db, org.id, None, {"thread_id": str(thread.id)}
        )
        # prompt must have truncated the long body: raw body alone exceeds
        # _BODY_LIMIT by far, so the sent content (header + truncated body)
        # must be much shorter than the raw body.
        assert len(captured["content"]) < len(long_body)
    finally:
        _teardown(db, org)


# ------------------------------------------------------- summarize thread


def test_summarize_persists_summary_on_fresh_row(db, monkeypatch):
    monkeypatch.setattr(
        "app.ai.model_router.complete",
        lambda messages, temperature=0.3: json.dumps(
            {"summary": "Customer needs urgent help restoring access to their account."}
        ),
    )

    org = _org(db)
    thread = _thread(db, org)

    try:
        result = MARKETING_TOOLS["summarize_email_thread"].handler(
            db, org.id, None, {"thread_id": str(thread.id)}
        )
        assert result["source"] == "llm"
        assert result["thread_id"] == str(thread.id)
        assert "restoring" in result["summary"]

        fresh = _fresh_thread(db, thread.id)
        assert fresh.summary == result["summary"]
    finally:
        _teardown(db, org)


def test_summarize_model_failure_falls_back_without_raising(db, monkeypatch):
    def boom(messages, temperature=0.3):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr("app.ai.model_router.complete", boom)

    org = _org(db)
    thread = _thread(db, org)

    try:
        result = MARKETING_TOOLS["summarize_email_thread"].handler(
            db, org.id, None, {"thread_id": str(thread.id)}
        )
        assert "error" not in result
        assert result["source"] == "data"
        assert result["summary"].strip()

        fresh = _fresh_thread(db, thread.id)
        assert fresh.summary == result["summary"]
    finally:
        _teardown(db, org)


def test_summarize_truncates_long_bodies(db, monkeypatch):
    captured = {}

    def fake(messages, temperature=0.3):
        captured["content"] = messages[1]["content"]
        return json.dumps({"summary": "Concise thread summary."})

    monkeypatch.setattr("app.ai.model_router.complete", fake)

    from app.models.email import Email, EmailThread

    org = _org(db)
    thread = EmailThread(organization_id=org.id, subject="Long thread", participants={})
    db.add(thread)
    db.flush()
    long_body = "details here " * 500
    db.add(
        Email(
            organization_id=org.id,
            thread_id=thread.id,
            body=long_body,
            direction="inbound",
        )
    )
    db.commit()
    db.refresh(thread)

    try:
        result = MARKETING_TOOLS["summarize_email_thread"].handler(
            db, org.id, None, {"thread_id": str(thread.id)}
        )
        assert result["summary"] == "Concise thread summary."
        assert len(captured["content"]) < len(long_body)
    finally:
        _teardown(db, org)