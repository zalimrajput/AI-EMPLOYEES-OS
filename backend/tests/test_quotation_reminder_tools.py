"""Quotation & reminder tool tests (against the live Postgres)."""
import os
import sys
import uuid

sys.path.insert(0, ".")

from decimal import Decimal

import pytest

from sqlalchemy import text

from app.ai.tools.invoice_tools import INVOICE_TOOLS
from app.ai.tools.reminder_tools import REMINDER_TOOLS


def _org(db):
    """Create a fresh org with a unique slug (never reuse a leftover one)."""
    from app.models.organization import Organization

    org = Organization(
        name="Audit Test Org",
        slug=f"audit-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _teardown(db, org):
    """Delete every row the tests created for this org.

    The seed attaches 12 AI employees to every org and that FK is NOT NULL
    without ondelete, so they must be deleted before the org row itself.
    Everything is removed via raw SQL in dependency order.
    """
    deletes = [
        "DELETE FROM quotation_items WHERE organization_id = :id",
        "DELETE FROM invoice_items WHERE organization_id = :id",
        "DELETE FROM storage_files WHERE organization_id = :id",
        "DELETE FROM quotations WHERE organization_id = :id",
        "DELETE FROM invoices WHERE organization_id = :id",
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


@pytest.mark.db
def test_create_quotation_computes_totals(db):
    from app.models.customer import Customer

    org = _org(db)
    cust = Customer(organization_id=org.id, name="Audit Customer")
    db.add(cust)
    db.commit()
    db.refresh(cust)

    try:
        res = INVOICE_TOOLS["create_quotation"].handler(
            db,
            org.id,
            None,
            {
                "customer_id": str(cust.id),
                "items": [
                    {"description": "Widget A", "quantity": 2, "unit_price": 10.00},
                    {"description": "Widget B", "quantity": 1, "unit_price": 5.50},
                ],
            },
        )
        assert res.get("id")
        assert Decimal(res["subtotal"]) == Decimal("25.50")
        assert Decimal(res["total"]) == Decimal("25.50")
        assert res["items"] == 2

        # PDF generation returns a real storage path/url AND a real file on
        # disk with nonzero size (not just "no exception").
        pdf = INVOICE_TOOLS["generate_quotation_pdf_tool"].handler(
            db, org.id, None, {"quotation_id": res["id"]}
        )
        assert not pdf.get("error")
        assert pdf.get("pdf_url")
        assert pdf.get("file")
        assert os.path.exists(pdf["file"]), f"pdf file missing: {pdf['file']}"
        assert os.path.getsize(pdf["file"]) > 0

        # Unknown quotation -> clean error
        err = INVOICE_TOOLS["generate_quotation_pdf_tool"].handler(
            db, org.id, None, {"quotation_id": str(uuid.uuid4())}
        )
        assert err.get("error")
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_executor_runs_reminder_through_guardrails(db):
    """End-to-end: executor.run must ALLOW create_reminder now.

    This is the real execution path (guardrails allowlist + per-agent
    allowlist), so it failed before create_reminder was added to
    _SAFE_TOOL_NAMES and succeeds now.
    """
    from app.ai.executor import run as execute
    from app.models.user import User

    org = _org(db)
    user = User(organization_id=org.id, full_name="Audit User")
    db.add(user)
    db.commit()
    db.refresh(user)
    try:
        res = execute(
            db,
            "create_reminder",
            org.id,
            str(user.id),
            {
                "target_type": "deal",
                "target_id": str(uuid.uuid4()),
                "remind_at": "2026-10-01T09:00:00Z",
                "message": "Follow up",
            },
            allowed_tools=["create_reminder"],
        )
        assert res.get("id"), f"expected success, got error: {res!r}"
        assert "not allowed" not in res  # guardrails must NOT reject it
        assert res["target_type"] == "deal"
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_reminder_crud(db):
    from app.models.user import User

    org = _org(db)
    user = User(organization_id=org.id, full_name="Audit User", email="audit@test.dev")
    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        rem = REMINDER_TOOLS["create_reminder"].handler(
            db,
            org.id,
            str(user.id),
            {
                "target_type": "deal",
                "target_id": str(uuid.uuid4()),
                "remind_at": "2026-09-01T10:00:00Z",
                "message": "Follow up if no reply",
            },
        )
        assert rem.get("id")
        assert rem["target_type"] == "deal"

        listed = REMINDER_TOOLS["list_reminders"].handler(
            db, org.id, None, {"target_type": "deal"}
        )
        assert any(r["id"] == rem["id"] for r in listed)

        all_upcoming = REMINDER_TOOLS["list_reminders"].handler(db, org.id, None, {})
        assert all_upcoming

        # Bad date -> structured error
        bad = REMINDER_TOOLS["create_reminder"].handler(
            db, org.id, None, {"target_type": "deal", "remind_at": "not-a-date"}
        )
        assert bad.get("error")
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_generate_invoice_pdf_writes_file(db):
    """generate_invoice_pdf_tool returns a real path/url and a real file."""
    from app.models.customer import Customer
    from app.models.invoice import Invoice

    org = _org(db)
    cust = Customer(organization_id=org.id, name="Invoice Customer")
    db.add(cust)
    db.commit()
    db.refresh(cust)
    invoice = Invoice(
        organization_id=org.id,
        customer_id=cust.id,
        invoice_number="INV-7",
        amount=Decimal("99.99"),
        status="unpaid",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    try:
        pdf = INVOICE_TOOLS["generate_invoice_pdf_tool"].handler(
            db, org.id, None, {"invoice_id": str(invoice.id)}
        )
        assert not pdf.get("error"), f"unexpected error: {pdf!r}"
        assert pdf.get("pdf_url")
        assert pdf.get("file")
        assert os.path.exists(pdf["file"]), f"pdf file missing: {pdf['file']}"
        assert os.path.getsize(pdf["file"]) > 0
        assert pdf["invoice_id"] == str(invoice.id)

        # Unknown invoice -> clean error
        err = INVOICE_TOOLS["generate_invoice_pdf_tool"].handler(
            db, org.id, None, {"invoice_id": str(uuid.uuid4())}
        )
        assert err.get("error")
    finally:
        _teardown(db, org)
