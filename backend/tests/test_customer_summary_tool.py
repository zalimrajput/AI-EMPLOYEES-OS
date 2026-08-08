"""summarize_customer tool tests (model_router.complete mocked; no LLM calls)."""
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, ".")

from decimal import Decimal

import pytest

from sqlalchemy import text

from app.ai.tools.crm_tools import CRM_TOOLS


def _org(db):
    from app.models.organization import Organization

    org = Organization(
        name="Summary Test Org",
        slug=f"summary-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _teardown(db, org):
    deletes = [
        "DELETE FROM quotation_items WHERE organization_id = :id",
        "DELETE FROM invoice_items WHERE organization_id = :id",
        "DELETE FROM storage_files WHERE organization_id = :id",
        "DELETE FROM quotations WHERE organization_id = :id",
        "DELETE FROM invoices WHERE organization_id = :id",
        "DELETE FROM deals WHERE organization_id = :id",
        "DELETE FROM pipelines WHERE organization_id = :id",
        "DELETE FROM activities WHERE organization_id = :id",
        "DELETE FROM customers WHERE organization_id = :id",
        "DELETE FROM storage_quotas WHERE organization_id = :id",
        "DELETE FROM reminders WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM ai_employees WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _customer(db, org, name="Acme Ltd"):
    from app.models.customer import Customer

    cust = Customer(organization_id=org.id, name=name, email="acme@example.com")
    db.add(cust)
    db.commit()
    db.refresh(cust)
    return cust


def _activity(db, org, cust, action, created_at):
    from app.models.activity import Activity

    db.add(
        Activity(
            organization_id=org.id,
            entity_type="customer",
            entity_id=cust.id,
            action=action,
            created_at=created_at,
        )
    )
    db.commit()


def _deal(db, org, cust, title, stage, value, created_at=None):
    from app.models.pipeline import Deal

    db.add(
        Deal(
            organization_id=org.id,
            customer_id=cust.id,
            title=title,
            stage=stage,
            value=value,
            probability=50,
            created_at=created_at,
        )
    )
    db.commit()


def _invoice(db, org, cust, status, total):
    from app.models.invoice import Invoice

    db.add(
        Invoice(
            organization_id=org.id,
            customer_id=cust.id,
            invoice_number=f"INV-{uuid.uuid4().hex[:6]}",
            amount=total,
            status=status,
        )
    )
    db.commit()


def test_summarize_customer_shapes_result(db, monkeypatch):
    now = datetime.now(timezone.utc)

    monkeypatch.setattr(
        "app.ai.tools.crm_tools.model_router.complete",
        lambda messages, temperature=0.3: (
            '{"summary": "Acme is an engaged customer with a healthy pipeline.", '
            '"relationship_health": "strong", '
            '"suggested_next_action": "Schedule a renewal call."}'
        ),
    )

    org = _org(db)
    cust = _customer(db, org)
    _activity(db, org, cust, "Scheduled discovery call", now - timedelta(days=5))
    _activity(db, org, cust, "Sent contract", now - timedelta(days=3))
    _deal(db, org, cust, "Expansion", "negotiation", Decimal("25000.00"))
    _deal(db, org, cust, "Closed one", "won", Decimal("1000.00"))
    _invoice(db, org, cust, "unpaid", Decimal("500.00"))

    try:
        result = CRM_TOOLS["summarize_customer"].handler(
            db, org.id, None, {"customer_id": str(cust.id)}
        )
        assert result["customer_id"] == str(cust.id)
        assert result["source"] == "llm"
        assert result["summary"] == "Acme is an engaged customer with a healthy pipeline."
        assert result["relationship_health"] == "strong"
        assert result["suggested_next_action"] == "Schedule a renewal call."
        assert result["open_deals_value"] == 25000.00
        assert result["last_contact_days_ago"] == 3
        assert any("unpaid invoice" in f for f in result["flags"])
    finally:
        _teardown(db, org)


def test_summarize_customer_zero_activity_returns_valid(db, monkeypatch):
    monkeypatch.setattr(
        "app.ai.tools.crm_tools.model_router.complete",
        lambda messages, temperature=0.3: "not valid json at all",
    )

    org = _org(db)
    cust = _customer(db, org, name="Quiet Corp")

    try:
        result = CRM_TOOLS["summarize_customer"].handler(
            db, org.id, None, {"customer_id": str(cust.id)}
        )
        assert result["customer_id"] == str(cust.id)
        assert "error" not in result
        assert result["source"] == "data"
        assert isinstance(result["summary"], str) and result["summary"]
        assert result["relationship_health"] == "neutral"
        assert result["open_deals_value"] == 0
        assert result["last_contact_days_ago"] is None
        assert any("no recorded pipeline or activity history" in f for f in result["flags"])
    finally:
        _teardown(db, org)


def test_summarize_customer_not_found(db, monkeypatch):
    called = {"n": 0}

    def boom(messages, temperature=0.3):
        called["n"] += 1
        raise AssertionError("should not be called")

    monkeypatch.setattr("app.ai.tools.crm_tools.model_router.complete", boom)

    org = _org(db)
    try:
        result = CRM_TOOLS["summarize_customer"].handler(
            db, org.id, None, {"customer_id": str(uuid.uuid4())}
        )
        assert result == {"error": "Customer not found"}
        assert called["n"] == 0
    finally:
        _teardown(db, org)


def test_summarize_customer_model_error_falls_back(db, monkeypatch):
    def boom(messages, temperature=0.3):
        raise RuntimeError("rate limit exceeded")

    monkeypatch.setattr("app.ai.tools.crm_tools.model_router.complete", boom)

    org = _org(db)
    cust = _customer(db, org)
    _deal(db, org, cust, "Big one", "proposal", Decimal("100000.00"))

    try:
        result = CRM_TOOLS["summarize_customer"].handler(
            db, org.id, None, {"customer_id": str(cust.id)}
        )
        assert "error" not in result
        assert result["source"] == "data"
        assert result["open_deals_value"] == 100000.00
        assert result["relationship_health"] in ("strong", "neutral", "at_risk")
        assert isinstance(result["summary"], str) and result["summary"]
    finally:
        _teardown(db, org)


def test_summarize_customer_at_risk_flags_from_data(db, monkeypatch):
    now = datetime.now(timezone.utc)

    monkeypatch.setattr(
        "app.ai.tools.crm_tools.model_router.complete",
        lambda messages, temperature=0.3: (
            '{"summary": "s", "relationship_health": "at_risk", '
            '"suggested_next_action": "a"}'
        ),
    )

    org = _org(db)
    cust = _customer(db, org)
    _activity(db, org, cust, "old note", now - timedelta(days=45))
    _deal(
        db,
        org,
        cust,
        "Stalled deal",
        "negotiation",
        Decimal("5000.00"),
        created_at=now - timedelta(days=90),
    )

    try:
        result = CRM_TOOLS["summarize_customer"].handler(
            db, org.id, None, {"customer_id": str(cust.id)}
        )
        assert result["last_contact_days_ago"] == 45
        flags = " ".join(result["flags"])
        assert "no contact in 30+ days" in flags
        assert "deal stalled" in flags
    finally:
        _teardown(db, org)
