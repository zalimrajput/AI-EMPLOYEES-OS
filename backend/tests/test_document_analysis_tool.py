"""analyze_document tool tests (model_router.complete mocked; no LLM calls)."""
import json
import sys
import uuid

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text

from app.ai.tools.knowledge_tools import DISCLAIMER, KNOWLEDGE_TOOLS, _TEXT_LIMIT


def _org(db):
    from app.models.organization import Organization

    org = Organization(
        name="Legal Test Org",
        slug=f"legal-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _teardown(db, org):
    deletes = [
        "DELETE FROM documents WHERE organization_id = :id",
        "DELETE FROM storage_files WHERE organization_id = :id",
        "DELETE FROM storage_quotas WHERE organization_id = :id",
        "DELETE FROM reminders WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM ai_employees WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _document(db, org, text_body=None):
    from app.models.document import Document

    doc = Document(
        organization_id=org.id,
        filename="contract.pdf",
        mime_type="application/pdf",
        extracted_text=text_body,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_analyze_document_shaped_result_with_disclaimer(db, monkeypatch):
    monkeypatch.setattr(
        "app.ai.tools.knowledge_tools.model_router.complete",
        lambda messages, temperature=0.3: json.dumps(
            {
                "summary": "A standard non-disclosure agreement.",
                "document_type": "NDA",
                "key_terms": [{"term": "Confidentiality period", "detail": "2 years"}],
                "risks": ["No governing law specified"],
                "missing_or_unusual": ["cap on liability absent"],
            }
        ),
    )

    org = _org(db)
    doc = _document(db, org, "This NDA governs confidential materials.")

    try:
        result = KNOWLEDGE_TOOLS["analyze_document"].handler(
            db, org.id, None, {"document_id": str(doc.id)}
        )
        assert result["source"] == "llm"
        assert result["summary"] == "A standard non-disclosure agreement."
        assert result["truncated"] is False
        assert result["disclaimer"] == DISCLAIMER
        assert result["document_type"] == "nda"
        assert len(result["key_terms"]) == 1
        assert result["key_terms"][0]["term"] == "Confidentiality period"
        assert result["risks"] == ["No governing law specified"]
        assert result["missing_or_unusual"] == ["cap on liability absent"]
    finally:
        _teardown(db, org)


def test_analyze_empty_text_errors_without_complete(db, monkeypatch):
    called = {"n": 0}

    def boom(messages, temperature=0.3):
        called["n"] += 1
        raise AssertionError("should not be called")

    monkeypatch.setattr("app.ai.tools.knowledge_tools.model_router.complete", boom)

    org = _org(db)
    doc = _document(db, org, "")

    try:
        result = KNOWLEDGE_TOOLS["analyze_document"].handler(
            db, org.id, None, {"document_id": str(doc.id)}
        )
        assert result == {"error": "Document has no extracted text to analyze"}
        assert called["n"] == 0
    finally:
        _teardown(db, org)


def test_analyze_document_not_found(db, monkeypatch):
    called = {"n": 0}

    def boom(messages, temperature=0.3):
        called["n"] += 1
        raise AssertionError("should not be called")

    monkeypatch.setattr("app.ai.tools.knowledge_tools.model_router.complete", boom)

    org = _org(db)
    try:
        result = KNOWLEDGE_TOOLS["analyze_document"].handler(
            db, org.id, None, {"document_id": str(uuid.uuid4())}
        )
        assert result == {"error": "Document not found"}
        assert called["n"] == 0
    finally:
        _teardown(db, org)


def test_analyze_model_error_falls_back_with_disclaimer(db, monkeypatch):
    def boom(messages, temperature=0.3):
        raise RuntimeError("rate limit exceeded")

    monkeypatch.setattr("app.ai.tools.knowledge_tools.model_router.complete", boom)

    org = _org(db)
    doc = _document(db, org, "Some contract text.")

    try:
        result = KNOWLEDGE_TOOLS["analyze_document"].handler(
            db, org.id, None, {"document_id": str(doc.id)}
        )
        assert result["source"] == "data"
        assert result["summary"] == "Automated analysis unavailable."
        assert result["document_type"] == "unknown"
        assert result["key_terms"] == []
        assert result["risks"] == []
        assert result["missing_or_unusual"] == []
        assert result["disclaimer"] == DISCLAIMER
    finally:
        _teardown(db, org)


def test_analyze_truncates_long_text(db, monkeypatch):
    captured = {}

    def fake(messages, temperature=0.3):
        captured["content"] = messages[1]["content"]
        return json.dumps(
            {"summary": "ok", "document_type": "unknown", "key_terms": [], "risks": [], "missing_or_unusual": []}
        )

    monkeypatch.setattr("app.ai.tools.knowledge_tools.model_router.complete", fake)

    org = _org(db)
    long_text = "recital about business purposes. " * 400
    doc = _document(db, org, long_text)

    try:
        result = KNOWLEDGE_TOOLS["analyze_document"].handler(
            db, org.id, None, {"document_id": str(doc.id)}
        )
        assert result["truncated"] is True
        assert len(captured["content"]) <= _TEXT_LIMIT
    finally:
        _teardown(db, org)