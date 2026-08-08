"""Real-DB smoke tests for marketing tools (list_campaigns, create_email_draft)."""
import sys
import uuid

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text


def _teardown(db, org):
    for statement in [
        "DELETE FROM emails WHERE organization_id = :id",
        "DELETE FROM email_threads WHERE organization_id = :id",
        "DELETE FROM marketing_campaigns WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _org(db):
    from app.models.organization import Organization

    org = Organization(name="Mkt Org", slug=f"mkt-{uuid.uuid4().hex[:10]}", settings={})
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.mark.db
def test_list_campaigns_handler_returns_real_row(db):
    from app.ai.tools.marketing_tools import MARKETING_TOOLS
    from app.models.marketing import MarketingCampaign

    org = _org(db)
    camp = MarketingCampaign(
        organization_id=org.id,
        name="Summer Launch",
        campaign_type="email",
        status="active",
        budget=5000,
    )
    db.add(camp)
    db.commit()
    db.refresh(camp)

    try:
        result = MARKETING_TOOLS["list_campaigns"].handler(db, org.id, None, {})
        assert any(c["id"] == str(camp.id) for c in result)
        row = next(c for c in result if c["id"] == str(camp.id))
        assert row["name"] == "Summer Launch"
        assert row["campaign_type"] == "email"
        assert row["status"] == "active"
        assert row["budget"] == 5000.0

        active = MARKETING_TOOLS["list_campaigns"].handler(
            db, org.id, None, {"status": "active"}
        )
        assert any(c["id"] == str(camp.id) for c in active)
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_create_email_draft_handler_persists_email_row(db):
    from app.ai.tools.marketing_tools import MARKETING_TOOLS
    from app.models.email import Email

    org = _org(db)

    try:
        result = MARKETING_TOOLS["create_email_draft"].handler(
            db,
            org.id,
            None,
            {
                "receiver": "lead@example.com",
                "subject": "Special offer",
                "body": "Hi, here is our special offer.",
            },
        )
        assert result.get("draft") is True
        assert result.get("subject") == "Special offer"

        email = db.query(Email).filter(Email.organization_id == org.id).first()
        assert email is not None
        assert email.receiver == "lead@example.com"
        assert email.direction == "outbound"
        assert email.ai_generated is True
    finally:
        _teardown(db, org)