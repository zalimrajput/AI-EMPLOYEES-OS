"""Workflow tests: on_invoice_paid chain + mark_invoice_paid AI tool."""
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, ".")

from decimal import Decimal

import pytest

from sqlalchemy import text

from app.ai.tools.invoice_tools import INVOICE_TOOLS


def _org(db):
    from app.models.organization import Organization

    org = Organization(
        name="Workflow Test Org",
        slug=f"wf-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _customer(db, org, name="Acme Customer"):
    from app.models.customer import Customer

    cust = Customer(
        organization_id=org.id,
        name=name,
        email="acme@example.com",
    )
    db.add(cust)
    db.commit()
    db.refresh(cust)
    return cust


def _invoice(db, org, customer, status="unpaid", number="INV-WF-1"):
    from app.models.invoice import Invoice

    inv = Invoice(
        organization_id=org.id,
        customer_id=customer.id,
        invoice_number=number,
        amount=Decimal("120.00"),
        status=status,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def _teardown(db, org):
    deletes = [
        "DELETE FROM quotation_items WHERE organization_id = :id",
        "DELETE FROM invoice_items WHERE organization_id = :id",
        "DELETE FROM storage_files WHERE organization_id = :id",
        "DELETE FROM quotations WHERE organization_id = :id",
        "DELETE FROM invoices WHERE organization_id = :id",
        "DELETE FROM notifications WHERE organization_id = :id",
        "DELETE FROM activities WHERE organization_id = :id",
        "DELETE FROM reminders WHERE organization_id = :id",
        "DELETE FROM customers WHERE organization_id = :id",
        "DELETE FROM storage_quotas WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM ai_employees WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


class _FakeClient:
    def __init__(self):
        self.sent = []

    def send_email(self, **kwargs):
        self.sent.append(kwargs)
        return {"status": "sent"}


def _mock_gmail(monkeypatch, fake):
    monkeypatch.setattr(
        "app.integrations.gmail.service.get_client",
        lambda db, org_id: fake,
    )
    return fake


def _count(db, model, org_id):
    from sqlalchemy import func

    return db.query(func.count(model.id)).filter(model.organization_id == org_id).scalar()


def test_on_invoice_paid_runs_full_chain(db, monkeypatch):
    from app.models.activity import Activity
    from app.models.notification import Notification
    from app.models.reminder import Reminder

    fake = _mock_gmail(monkeypatch, _FakeClient())

    org = _org(db)
    cust = _customer(db, org)
    inv = _invoice(db, org, cust)

    try:
        from app.services.workflow_service import on_invoice_paid

        result = on_invoice_paid(db, org.id, inv.id)

        assert result["receipt"] is True
        assert result["crm_logged"] is True
        assert result["notified"] is True
        assert result["email_sent"] is True
        assert result["reminder_created"] is True

        # real rows, not just the returned dict
        assert _count(db, Activity, org.id) == 1
        assert _count(db, Notification, org.id) == 1
        assert _count(db, Reminder, org.id) == 1
        assert len(fake.sent) == 1
        assert "acme@example.com" in fake.sent[0]["to"]

        activity = db.query(Activity).filter(Activity.organization_id == org.id).first()
        assert activity.entity_type == "customer"
        assert activity.entity_id == cust.id
        assert "paid" in (activity.action or "")

        reminder = db.query(Reminder).filter(Reminder.organization_id == org.id).first()
        assert reminder.message and "Acme Customer" in reminder.message
        assert reminder.remind_at > datetime.now(timezone.utc)
    finally:
        _teardown(db, org)


def test_on_invoice_paid_email_failure_does_not_block_others(db, monkeypatch):
    from app.integrations.gmail.client import IntegrationNotConnectedError
    from app.models.activity import Activity
    from app.models.notification import Notification
    from app.models.reminder import Reminder

    def raise_not_connected(db, org_id):
        raise IntegrationNotConnectedError("not connected")

    monkeypatch.setattr(
        "app.integrations.gmail.service.get_client", raise_not_connected
    )

    org = _org(db)
    cust = _customer(db, org)
    inv = _invoice(db, org, cust)

    try:
        from app.services.workflow_service import on_invoice_paid

        result = on_invoice_paid(db, org.id, inv.id)

        assert result["email_sent"] is False
        assert result["crm_logged"] is True
        assert result["notified"] is True
        assert result["reminder_created"] is True
        assert result["receipt"] is True

        assert _count(db, Activity, org.id) == 1
        assert _count(db, Notification, org.id) == 1
        assert _count(db, Reminder, org.id) == 1
    finally:
        _teardown(db, org)


def test_mark_invoice_paid_tool_triggers_chain(db, monkeypatch):
    from app.models.activity import Activity
    from app.models.invoice import Invoice
    from app.models.reminder import Reminder

    fake = _mock_gmail(monkeypatch, _FakeClient())

    org = _org(db)
    cust = _customer(db, org)
    inv = _invoice(db, org, cust, status="unpaid")

    try:
        result = INVOICE_TOOLS["mark_invoice_paid"].handler(
            db, org.id, None, {"invoice_id": str(inv.id)}
        )
        assert result["status"] == "paid"
        assert result["workflow"]["crm_logged"] is True
        assert result["workflow"]["email_sent"] is True

        fresh = db.query(Invoice).filter(Invoice.id == inv.id).first()
        assert fresh.status == "paid"
        assert _count(db, Activity, org.id) == 1
        assert _count(db, Reminder, org.id) == 1
        assert len(fake.sent) == 1
    finally:
        _teardown(db, org)


def test_remarking_paid_invoice_does_not_refire(db, monkeypatch):
    from app.models.activity import Activity
    from app.models.reminder import Reminder

    fake = _mock_gmail(monkeypatch, _FakeClient())

    org = _org(db)
    cust = _customer(db, org)
    inv = _invoice(db, org, cust, status="paid")

    try:
        result = INVOICE_TOOLS["mark_invoice_paid"].handler(
            db, org.id, None, {"invoice_id": str(inv.id)}
        )
        assert result["workflow"] is None
        assert "already paid" in result["note"]

        # no duplicate side-effects
        assert _count(db, Activity, org.id) == 0
        assert _count(db, Reminder, org.id) == 0
        assert len(fake.sent) == 0
    finally:
        _teardown(db, org)