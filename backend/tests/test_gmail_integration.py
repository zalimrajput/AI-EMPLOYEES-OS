"""Gmail integration tests (httpx mocked; no real Google API calls)."""
import base64
import email
import re
import sys
import uuid

sys.path.insert(0, ".")

from decimal import Decimal

import pytest

from sqlalchemy import text


class FakeResp:
    def __init__(self, status_code, payload=None, text=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text if text is not None else str(payload)

    def json(self):
        return self._payload


class _Empty:
    def filter(self, *a, **k):
        return self

    def first(self):
        return None


class _FakeDB:
    def query(self, model):
        return _Empty()


def _org(db):
    from app.models.organization import Organization

    org = Organization(
        name="Gmail Test Org",
        slug=f"gmail-{uuid.uuid4().hex[:10]}",
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
        "DELETE FROM customers WHERE organization_id = :id",
        "DELETE FROM storage_quotas WHERE organization_id = :id",
        "DELETE FROM reminders WHERE organization_id = :id",
        "DELETE FROM meetings WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM integrations WHERE organization_id = :id",
        "DELETE FROM ai_employees WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def test_send_email_success(monkeypatch):
    from app.integrations.gmail.client import GmailClient

    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url))
        return FakeResp(200, {"id": "m1", "threadId": "t1"})

    monkeypatch.setattr("app.integrations.gmail.client.httpx.request", fake_request)

    client = GmailClient(
        db=None,
        organization_id="org",
        access_token="tok",
        refresh_token="rt",
        client_id="cid",
        client_secret="cs",
    )
    result = client.send_email("a@b.com", "Subject", "Body", cc="c@d.com")
    assert result == {"id": "m1", "thread_id": "t1", "status": "sent"}
    assert calls == [("POST", "https://gmail.googleapis.com/gmail/v1/users/me/messages/send")]


def test_refresh_then_retry_success(monkeypatch, db):
    from app.integrations.gmail.client import GmailClient
    from app.models.integration import Integration
    from app.utils.encryption import decrypt_value, encrypt_value

    org = _org(db)
    db.add(
        Integration(
            organization_id=org.id,
            provider="gmail",
            connected=True,
            access_token=encrypt_value("old_access"),
            refresh_token=encrypt_value("old_refresh"),
        )
    )
    db.commit()

    responses = [
        FakeResp(401, text="invalid_grant"),
        FakeResp(200, {"id": "m2", "threadId": "t2"}),
    ]

    def fake_request(method, url, **kwargs):
        return responses.pop(0)

    def fake_post(url, **kwargs):
        assert url == "https://oauth2.googleapis.com/token"
        assert kwargs["data"]["grant_type"] == "refresh_token"
        return FakeResp(200, {"access_token": "new_access", "refresh_token": "new_refresh"})

    monkeypatch.setattr("app.integrations.gmail.client.httpx.request", fake_request)
    monkeypatch.setattr("app.integrations.gmail.client.httpx.post", fake_post)

    try:
        client = GmailClient(
            db=db,
            organization_id=org.id,
            access_token="old_access",
            refresh_token="old_refresh",
            client_id="cid",
            client_secret="cs",
        )
        result = client.send_email("b@c.com", "Subj", "Body")
        assert result["id"] == "m2"
        assert client._access_token == "new_access"
        row = (
            db.query(Integration)
            .filter(
                Integration.organization_id == org.id,
                Integration.provider == "gmail",
            )
            .first()
        )
        assert decrypt_value(row.access_token) == "new_access"
        assert decrypt_value(row.refresh_token) == "new_refresh"
    finally:
        _teardown(db, org)


def test_refresh_failure_raises_auth_error(monkeypatch):
    from app.integrations.gmail.client import GmailClient, IntegrationAuthError

    def fake_request(method, url, **kwargs):
        return FakeResp(401, text="expired")

    def fake_post(url, **kwargs):
        return FakeResp(400, text="bad grant")

    monkeypatch.setattr("app.integrations.gmail.client.httpx.request", fake_request)
    monkeypatch.setattr("app.integrations.gmail.client.httpx.post", fake_post)

    client = GmailClient(
        db=None,
        organization_id="org",
        access_token="tok",
        refresh_token="rt",
        client_id="cid",
        client_secret="cs",
    )
    with pytest.raises(IntegrationAuthError):
        client.send_email("a@b.com", "S", "B")


def test_list_recent_messages_success(monkeypatch):
    from app.integrations.gmail.client import GmailClient

    def fake_request(method, url, **kwargs):
        assert kwargs["params"]["q"] == "from:me"
        return FakeResp(200, {"messages": [{"id": "a", "threadId": "t1"}]})

    monkeypatch.setattr("app.integrations.gmail.client.httpx.request", fake_request)
    client = GmailClient(
        db=None, organization_id="org", access_token="tok", refresh_token="rt"
    )
    result = client.list_recent_messages(query="from:me", max_results=5)
    assert result == [{"id": "a", "thread_id": "t1"}]


def test_not_connected_raises():
    from app.integrations.gmail.client import IntegrationNotConnectedError
    from app.integrations.gmail.service import get_client

    with pytest.raises(IntegrationNotConnectedError):
        get_client(_FakeDB(), "org")


def test_tool_returns_structured_error_when_not_connected(db):
    from app.ai.tools.email_tools import EMAIL_TOOLS

    org = _org(db)
    try:
        result = EMAIL_TOOLS["send_email"].handler(
            db,
            org.id,
            None,
            {"to": "x@y.com", "subject": "S", "body": "B"},
        )
        assert "error" in result
        assert "connect it in Settings" in result["error"]
    finally:
        _teardown(db, org)


def test_send_email_registered_and_allowlisted():
    """Lock down the registered-tool-but-missing-from-allowlist bug class."""
    from app.ai.guardrails import _SAFE_TOOL_NAMES, validate_tool_call
    from app.ai.tools import ALL_TOOLS, get_tool

    assert "send_email" in ALL_TOOLS
    assert get_tool("send_email") is not None
    assert "send_email" in _SAFE_TOOL_NAMES
    assert validate_tool_call("send_email", {})


def _normalize_pdf(data: bytes) -> bytes:
    """Blank per-render reportlab fields so two renders compare byte-equal.

    Length-preserving (xref offsets must stay valid), and strips the random
    /ID trailer plus the second-granularity CreationDate.
    """
    data = re.sub(
        rb"(/[A-Za-z]+Date\s*\(D:)[0-9]{14}([-+][0-9]{2}'[0-9]{2}'?\))?",
        lambda m: m.group(1)
        + b"00000000000000"
        + (m.group(2) if m.group(2) else b")"),
        data,
    )
    data = re.sub(
        rb"(/ID\s*\[\s*)(<[0-9a-f]{32}>)(\s*)(<[0-9a-f]{32}>)(\s*\])",
        lambda m: m.group(1)
        + b"<" + b"0" * 32 + b">"
        + m.group(3)
        + b"<" + b"0" * 32 + b">"
        + m.group(5),
        data,
    )
    return data


def _decoded_message(raw_b64: str):
    """Parse with the modern EmailMessage API (what GmailClient uses)."""
    from email.message import EmailMessage

    return email.message_from_bytes(
        base64.urlsafe_b64decode(raw_b64), _class=EmailMessage
    )


def test_send_email_with_attachment_multipart(monkeypatch):
    from app.integrations.gmail.client import GmailClient

    captured = {}

    def fake_request(method, url, **kwargs):
        captured["raw"] = kwargs["json"]["raw"]
        return FakeResp(200, {"id": "m1", "threadId": "t1"})

    monkeypatch.setattr("app.integrations.gmail.client.httpx.request", fake_request)

    client = GmailClient(
        db=None,
        organization_id="org",
        access_token="tok",
        refresh_token="rt",
        client_id="cid",
        client_secret="cs",
    )
    doc = b"%PDF-1.4 fake pdf bytes \x00\x01"
    result = client.send_email(
        "a@b.com",
        "Subject",
        "Body",
        attachments=[
            {
                "filename": "Quotation-Q1.pdf",
                "content_bytes": doc,
                "mime_type": "application/pdf",
            }
        ],
    )
    assert result["status"] == "sent"

    msg = _decoded_message(captured["raw"])
    assert msg.is_multipart()
    assert msg.get_content_maintype() == "multipart"
    attachments = list(msg.iter_attachments())
    assert len(attachments) == 1
    part = attachments[0]
    assert part.get_filename() == "Quotation-Q1.pdf"
    assert part.get_content_type() == "application/pdf"
    assert part.get_payload(decode=True) == doc


def test_send_email_without_attachments_is_plain(monkeypatch):
    """Regression: no-attachments path must stay a plain single-part message."""
    from app.integrations.gmail.client import GmailClient

    captured = {}

    def fake_request(method, url, **kwargs):
        captured["raw"] = kwargs["json"]["raw"]
        return FakeResp(200, {"id": "m1", "threadId": "t1"})

    monkeypatch.setattr("app.integrations.gmail.client.httpx.request", fake_request)

    client = GmailClient(
        db=None,
        organization_id="org",
        access_token="tok",
        refresh_token="rt",
        client_id="cid",
        client_secret="cs",
    )
    client.send_email("a@b.com", "Subject", "Body")
    msg = _decoded_message(captured["raw"])
    assert not msg.is_multipart()
    assert msg.get_content_type() == "text/plain"


@pytest.mark.db
def test_send_quotation_email_attaches_pdf(db, monkeypatch):
    from app.ai.tools.email_tools import EMAIL_TOOLS
    from app.models.customer import Customer
    from app.models.quotation import Quotation, QuotationItem
    from app.services.invoice_service import generate_quotation_pdf

    org = _org(db)
    cust = Customer(organization_id=org.id, name="PDF Customer")
    db.add(cust)
    db.commit()
    db.refresh(cust)
    quotation = Quotation(
        organization_id=org.id,
        customer_id=cust.id,
        quotation_number="QUO-42",
        status="approved",
        subtotal=Decimal("25.50"),
        tax=Decimal("0"),
        discount=Decimal("0"),
        total=Decimal("25.50"),
    )
    db.add(quotation)
    db.commit()
    db.refresh(quotation)
    db.add(
        QuotationItem(
            organization_id=org.id,
            quotation_id=quotation.id,
            description="Item",
            quantity=1,
            unit_price=Decimal("25.50"),
            tax_rate=Decimal("0"),
            line_total=Decimal("25.50"),
            sort_order=0,
        )
    )
    db.commit()

    expected = generate_quotation_pdf(db, org.id, quotation).getvalue()

    captured = {}

    def fake_request(method, url, **kwargs):
        captured["raw"] = kwargs["json"]["raw"]
        return FakeResp(200, {"id": "m9", "threadId": "t9"})

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

    try:
        result = EMAIL_TOOLS["send_quotation_email"].handler(
            db,
            org.id,
            None,
            {
                "quotation_id": str(quotation.id),
                "to": "john@acme.com",
                "subject": "Your quotation",
                "body": "See attached.",
            },
        )
        assert result.get("status") == "sent"
        assert "error" not in result

        msg = _decoded_message(captured["raw"])
        assert msg.is_multipart()
        attachments = list(msg.iter_attachments())
        assert len(attachments) == 1
        part = attachments[0]
        assert part.get_filename() == "Quotation-QUO-42.pdf"
        assert part.get_content_type() == "application/pdf"
        assert _normalize_pdf(expected) == _normalize_pdf(
            part.get_payload(decode=True)
        )
    finally:
        _teardown(db, org)
