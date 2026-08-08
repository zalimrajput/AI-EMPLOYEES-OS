"""followup_worker tests: stale-contact reminders are created, deduped."""
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text

from workers.followup_worker import check_stale_customer_threads


def _org(db):
    from app.models.organization import Organization

    org = Organization(
        name="Followup Org",
        slug=f"followup-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _customer(db, org, name="Acme"):
    from app.models.customer import Customer

    cust = Customer(organization_id=org.id, name=name)
    db.add(cust)
    db.commit()
    db.refresh(cust)
    return cust


def _deal(db, org, customer, title="Big deal"):
    from app.models.pipeline import Deal

    deal = Deal(
        organization_id=org.id,
        customer_id=customer.id,
        title=title,
        stage="negotiation",
        value=1000,
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


def _activity(db, org, customer, created_at):
    from app.models.activity import Activity

    db.add(
        Activity(
            organization_id=org.id,
            entity_type="customer",
            entity_id=customer.id,
            action="contacted",
            created_at=created_at,
        )
    )
    db.commit()


def _teardown(db, org):
    deletes = [
        "DELETE FROM reminders WHERE organization_id = :id",
        "DELETE FROM activities WHERE organization_id = :id",
        "DELETE FROM deals WHERE organization_id = :id",
        "DELETE FROM customers WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM ai_employees WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _count_reminders(db, org_id):
    from sqlalchemy import func

    from app.models.reminder import Reminder

    return (
        db.query(func.count(Reminder.id))
        .filter(Reminder.organization_id == org_id)
        .scalar()
    )


@pytest.mark.db
def test_stale_customer_gets_reminder(db):
    from app.models.reminder import Reminder

    org = _org(db)
    cust = _customer(db, org, "Acme")
    deal = _deal(db, org, cust)
    now = datetime.now(timezone.utc)
    _activity(db, org, cust, now - timedelta(days=10))  # stale

    try:
        result = check_stale_customer_threads(
            stale_days=3, organization_id=str(org.id)
        )
        assert result["created"] == 1
        reminder = (
            db.query(Reminder)
            .filter(Reminder.organization_id == org.id)
            .first()
        )
        assert reminder is not None
        assert reminder.target_type == "deal"
        assert reminder.target_id == deal.id
        assert "Acme" in reminder.message
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_recent_customer_no_reminder(db):
    org = _org(db)
    cust = _customer(db, org, "Recent Co")
    _deal(db, org, cust, "Deal")
    now = datetime.now(timezone.utc)
    _activity(db, org, cust, now - timedelta(hours=2))  # recent

    try:
        result = check_stale_customer_threads(
            stale_days=3, organization_id=str(org.id)
        )
        assert result["created"] == 0
        assert _count_reminders(db, org.id) == 0
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_no_duplicate_on_second_run(db):
    org = _org(db)
    cust = _customer(db, org, "Dupe Co")
    _deal(db, org, cust)
    now = datetime.now(timezone.utc)
    _activity(db, org, cust, now - timedelta(days=5))

    try:
        first = check_stale_customer_threads(
            stale_days=3, organization_id=str(org.id)
        )
        assert first["created"] == 1
        second = check_stale_customer_threads(
            stale_days=3, organization_id=str(org.id)
        )
        assert second["created"] == 0
        assert _count_reminders(db, org.id) == 1
    finally:
        _teardown(db, org)