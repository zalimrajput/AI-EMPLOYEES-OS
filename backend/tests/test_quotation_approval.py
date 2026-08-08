"""Quotation approval workflow tests (real DB, Gmail mocked; no real calls)."""
import sys
import uuid

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text


class FakeResp:
    def __init__(self, status_code, payload=None, text=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text if text is not None else str(payload)

    def json(self):
        return self._payload


def _teardown(db, org):
    deletes = [
        "DELETE FROM activities WHERE organization_id = :id",
        "DELETE FROM storage_files WHERE organization_id = :id",
        "DELETE FROM quotation_items WHERE organization_id = :id",
        "DELETE FROM quotations WHERE organization_id = :id",
        "DELETE FROM customers WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _org(db):
    from app.models.organization import Organization

    org = Organization(
        name="Approval Org",
        slug=f"approval-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _email_tools():
    from app.ai.tools.email_tools import EMAIL_TOOLS

    return EMAIL_TOOLS


def _mock_gmail(monkeypatch):
    captured = {}

    def fake_request(method, url, **kwargs):
        captured["raw"] = kwargs["json"]["raw"]
        return FakeResp(200, {"id": "m1", "threadId": "t1"})

    monkeypatch.setattr("app.integrations.gmail.client.httpx.request", fake_request)

    from app.integrations.gmail.client import GmailClient

    monkeypatch.setattr(
        "app.integrations.gmail.service.get_client",
        lambda db, org_id: GmailClient(
            db=None,
            organization_id=org_id,
            access_token="tok",
            refresh_token="rt",
            client_id="cid",
            client_secret="cs",
        ),
    )
    return captured


def _create_quotation(db, org):
    from app.ai.tools.invoice_tools import INVOICE_TOOLS

    result = INVOICE_TOOLS["create_quotation"].handler(
        db,
        org.id,
        None,
        {
            "items": [
                {
                    "description": "Consulting",
                    "quantity": 2,
                    "unit_price": 100.00,
                    "tax_rate": 5.0,
                }
            ],
        },
    )
    assert "error" not in result, result
    assert result["status"] == "draft"
    return result


def _quotation_status(db, quotation_id):
    from app.models.quotation import Quotation

    row = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    return row.status if row else None


@pytest.mark.db
def test_quotation_approval_happy_path_draft_to_sent(db, monkeypatch):
    from app.ai.tools.invoice_tools import INVOICE_TOOLS

    _mock_gmail(monkeypatch)
    org = _org(db)
    try:
        q = _create_quotation(db, org)

        submitted = INVOICE_TOOLS["submit_quotation_for_approval"].handler(
            db, org.id, None, {"quotation_id": q["id"]}
        )
        assert "error" not in submitted, submitted
        assert submitted["status"] == "pending_approval"
        assert _quotation_status(db, q["id"]) == "pending_approval"

        approved = INVOICE_TOOLS["approve_quotation"].handler(
            db, org.id, None, {"quotation_id": q["id"], "notes": "Approved by finance"}
        )
        assert "error" not in approved, approved
        assert approved["status"] == "approved"
        assert _quotation_status(db, q["id"]) == "approved"

        sent = _email_tools()["send_quotation_email"].handler(
            db,
            org.id,
            None,
            {"quotation_id": q["id"], "to": "cust@acme.com", "subject": "Your quotation"},
        )
        assert "error" not in sent, sent
        assert sent.get("status") == "sent"
        assert _quotation_status(db, q["id"]) == "sent"
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_quotation_reject_path_send_blocked(db, monkeypatch):
    from app.ai.tools.invoice_tools import INVOICE_TOOLS

    _mock_gmail(monkeypatch)
    org = _org(db)
    try:
        q = _create_quotation(db, org)

        INVOICE_TOOLS["submit_quotation_for_approval"].handler(
            db, org.id, None, {"quotation_id": q["id"]}
        )
        rejected = INVOICE_TOOLS["reject_quotation"].handler(
            db, org.id, None, {"quotation_id": q["id"], "reason": "Price too high"}
        )
        assert "error" not in rejected, rejected
        assert rejected["status"] == "rejected"
        assert _quotation_status(db, q["id"]) == "rejected"

        sent = _email_tools()["send_quotation_email"].handler(
            db, org.id, None, {"quotation_id": q["id"], "to": "cust@acme.com"}
        )
        assert "error" in sent
        assert "currently in status: rejected" in sent["error"]
        assert _quotation_status(db, q["id"]) == "rejected"
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_quotation_invalid_transitions_return_structured_errors(db):
    from app.ai.tools.invoice_tools import INVOICE_TOOLS

    org = _org(db)
    try:
        q = _create_quotation(db, org)

        approve_draft = INVOICE_TOOLS["approve_quotation"].handler(
            db, org.id, None, {"quotation_id": q["id"]}
        )
        assert "error" in approve_draft
        assert "pending_approval" in approve_draft["error"]
        assert _quotation_status(db, q["id"]) == "draft"

        reject_draft = INVOICE_TOOLS["reject_quotation"].handler(
            db, org.id, None, {"quotation_id": q["id"], "reason": "no"}
        )
        assert "error" in reject_draft
        assert _quotation_status(db, q["id"]) == "draft"

        reject_no_reason = INVOICE_TOOLS["reject_quotation"].handler(
            db, org.id, None, {"quotation_id": q["id"]}
        )
        assert "error" in reject_no_reason
        assert "reason" in reject_no_reason["error"]

        INVOICE_TOOLS["submit_quotation_for_approval"].handler(
            db, org.id, None, {"quotation_id": q["id"]}
        )
        INVOICE_TOOLS["approve_quotation"].handler(db, org.id, None, {"quotation_id": q["id"]})

        double_approve = INVOICE_TOOLS["approve_quotation"].handler(
            db, org.id, None, {"quotation_id": q["id"]}
        )
        assert "error" in double_approve
        assert "pending_approval" in double_approve["error"]
        assert _quotation_status(db, q["id"]) == "approved"

        resubmit = INVOICE_TOOLS["submit_quotation_for_approval"].handler(
            db, org.id, None, {"quotation_id": q["id"]}
        )
        assert "error" in resubmit
        assert _quotation_status(db, q["id"]) == "approved"

        missing = INVOICE_TOOLS["approve_quotation"].handler(
            db, org.id, None, {"quotation_id": str(uuid.uuid4())}
        )
        assert missing == {"error": "Quotation not found"}
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_send_unapproved_quotation_reports_actual_status(db, monkeypatch):
    from app.ai.tools.invoice_tools import INVOICE_TOOLS

    _mock_gmail(monkeypatch)
    org = _org(db)
    try:
        q = _create_quotation(db, org)

        result = _email_tools()["send_quotation_email"].handler(
            db, org.id, None, {"quotation_id": q["id"], "to": "cust@acme.com"}
        )
        assert "error" in result
        assert "Quotation must be approved before sending" in result["error"]
        assert "status: draft" in result["error"]
        assert _quotation_status(db, q["id"]) == "draft"
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_quotation_transitions_log_crm_activity(db):
    from app.ai.tools.invoice_tools import INVOICE_TOOLS
    from app.models.activity import Activity

    org = _org(db)
    try:
        q = _create_quotation(db, org)
        INVOICE_TOOLS["submit_quotation_for_approval"].handler(
            db, org.id, None, {"quotation_id": q["id"]}
        )
        INVOICE_TOOLS["approve_quotation"].handler(
            db, org.id, None, {"quotation_id": q["id"], "notes": "OK"}
        )

        rows = (
            db.query(Activity)
            .filter(Activity.organization_id == org.id, Activity.entity_type == "quotation")
            .all()
        )
        actions = [row.action for row in rows]
        assert "Quotation submitted for approval" in actions
        assert "Quotation approved" in actions
    finally:
        _teardown(db, org)
