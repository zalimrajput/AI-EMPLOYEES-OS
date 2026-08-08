"""CRM service tests using the live database (auto-skipped when offline)."""
import sys
import uuid

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text


def _teardown(db, org):
    for statement in [
        "DELETE FROM invoices WHERE organization_id = :id",
        "DELETE FROM quotation_items WHERE organization_id = :id",
        "DELETE FROM quotations WHERE organization_id = :id",
        "DELETE FROM deals WHERE organization_id = :id",
        "DELETE FROM pipelines WHERE organization_id = :id",
        "DELETE FROM activities WHERE organization_id = :id",
        "DELETE FROM customers WHERE organization_id = :id",
        "DELETE FROM leads WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM ai_employees WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]:
        db.execute(text(statement), {"id": org.id})
    db.commit()


@pytest.mark.db
def test_crm_stats(db):
    from app.services.crm_service import get_crm_stats

    from app.models.organization import Organization

    org = db.query(Organization).order_by(Organization.created_at).first()
    if org is None:
        pytest.skip("no orgs in database")
    stats = get_crm_stats(db, org.id)
    assert isinstance(stats, dict)
    assert "customers_total" in stats
    assert "leads_total" in stats


@pytest.mark.db
def test_billing_overview(db):
    from app.models.organization import Organization
    from app.services.billing_service import get_billing_overview

    org = db.query(Organization).order_by(Organization.created_at).first()
    if org is None:
        pytest.skip("no orgs in database")
    overview = get_billing_overview(db, org.id)
    assert "plans" in overview
    assert "usage" in overview
    assert "subscription" in overview


@pytest.mark.db
def test_org_settings_defaults(db):
    from app.models.organization import Organization
    from app.services.organization_settings_service import get_settings

    org = db.query(Organization).order_by(Organization.created_at).first()
    if org is None:
        pytest.skip("no orgs in database")
    settings = get_settings(db, org.id)
    assert settings is not None


@pytest.mark.db
def test_create_activity_handler_persists_real_row(db):
    """create_activity must persist a real Activity row via the real handler."""
    from app.ai.tools.crm_tools import CRM_TOOLS
    from app.models.activity import Activity
    from app.models.customer import Customer
    from app.models.organization import Organization

    org = Organization(
        name="CRM Tool Test Org",
        slug=f"crm-tool-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    customer = Customer(
        organization_id=org.id,
        name="Acme Test Co",
        email="acme-test@example.com",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    try:
        handler = CRM_TOOLS["create_activity"].handler
        result = handler(
            db,
            org.id,
            None,
            {
                "target_type": "customer",
                "target_id": str(customer.id),
                "type": "note",
                "description": "Initial onboarding call done.",
            },
        )
        assert result.get("created") is True

        activity = (
            db.query(Activity)
            .filter(
                Activity.organization_id == org.id,
                Activity.entity_type == "customer",
                Activity.entity_id == customer.id,
            )
            .first()
        )
        assert activity is not None
        assert activity.entity_id == customer.id
        assert activity.action == "Initial onboarding call done."
        assert (activity.metadata_json or {}).get("source") == "ai"
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_search_crm_handler_matches_real_customers_and_leads(db):
    from app.ai.tools.crm_tools import CRM_TOOLS
    from app.models.customer import Customer
    from app.models.lead import Lead
    from app.models.organization import Organization

    org = Organization(name="CRM Org", slug=f"crm-{uuid.uuid4().hex[:10]}", settings={})
    db.add(org)
    db.commit()
    db.refresh(org)

    customer = Customer(
        organization_id=org.id, name="Globex Inc", email="sales@globex.com"
    )
    lead = Lead(organization_id=org.id, name="Alice", company="Initech")
    db.add_all([customer, lead])
    db.commit()
    db.refresh(customer)
    db.refresh(lead)

    try:
        result = CRM_TOOLS["search_crm"].handler(
            db, org.id, None, {"query": "globex", "entity": "all"}
        )
        customer_ids = [c["id"] for c in result["customers"]]
        assert str(customer.id) in customer_ids

        result_leads = CRM_TOOLS["search_crm"].handler(
            db, org.id, None, {"query": "initech", "entity": "lead"}
        )
        lead_ids = [l["id"] for l in result_leads["leads"]]
        assert str(lead.id) in lead_ids
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_get_customer_handler_returns_real_row(db):
    from app.ai.tools.crm_tools import CRM_TOOLS
    from app.models.customer import Customer
    from app.models.organization import Organization

    org = Organization(name="CRM Org", slug=f"crm-{uuid.uuid4().hex[:10]}", settings={})
    db.add(org)
    db.commit()
    db.refresh(org)

    customer = Customer(
        organization_id=org.id, name="Umbrella Corp", email="ceo@umbrella.com"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    try:
        result = CRM_TOOLS["get_customer"].handler(
            db, org.id, None, {"id": str(customer.id)}
        )
        assert result["name"] == "Umbrella Corp"
        assert result["email"] == "ceo@umbrella.com"

        missing = CRM_TOOLS["get_customer"].handler(
            db, org.id, None, {"id": str(uuid.uuid4())}
        )
        assert missing.get("error")
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_list_leads_handler_matches_status_filter(db):
    from app.ai.tools.crm_tools import CRM_TOOLS
    from app.models.lead import Lead
    from app.models.organization import Organization

    org = Organization(name="CRM Org", slug=f"crm-{uuid.uuid4().hex[:10]}", settings={})
    db.add(org)
    db.commit()
    db.refresh(org)

    l1 = Lead(organization_id=org.id, name="Bob", status="new")
    l2 = Lead(organization_id=org.id, name="Carol", status="qualified")
    db.add_all([l1, l2])
    db.commit()
    db.refresh(l1)
    db.refresh(l2)

    try:
        qualified = CRM_TOOLS["list_leads"].handler(
            db, org.id, None, {"status": "qualified"}
        )
        assert len(qualified) == 1
        assert qualified[0]["id"] == str(l2.id)
        assert qualified[0]["status"] == "qualified"
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_list_deals_handler_returns_real_rows(db):
    from app.ai.tools.crm_tools import CRM_TOOLS
    from app.models.organization import Organization
    from app.models.pipeline import Deal

    org = Organization(name="CRM Org", slug=f"crm-{uuid.uuid4().hex[:10]}", settings={})
    db.add(org)
    db.commit()
    db.refresh(org)

    deal = Deal(organization_id=org.id, title="Enterprise License", stage="proposal")
    db.add(deal)
    db.commit()
    db.refresh(deal)

    try:
        result = CRM_TOOLS["list_deals"].handler(db, org.id, None, {})
        assert any(d["id"] == str(deal.id) for d in result)
        deal_row = next(d for d in result if d["id"] == str(deal.id))
        assert deal_row["title"] == "Enterprise License"
        assert deal_row["stage"] == "proposal"
    finally:
        _teardown(db, org)