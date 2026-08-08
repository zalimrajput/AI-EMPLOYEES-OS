"""Google Calendar integration + meeting-sync tests (httpx mocked)."""
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
        name="Calendar Test Org",
        slug=f"cal-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _teardown(db, org):
    deletes = [
        "DELETE FROM meetings WHERE organization_id = :id",
        "DELETE FROM integrations WHERE organization_id = :id",
        "DELETE FROM ai_employees WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


def test_create_event_success(monkeypatch):
    from app.integrations.google_calendar.client import GoogleCalendarClient

    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs.get("json")))
        return FakeResp(
            200,
            {"id": "ev1", "htmlLink": "https://calendar.google.com/ev1"},
        )

    monkeypatch.setattr(
        "app.integrations.google_calendar.client.httpx.request", fake_request
    )
    client = GoogleCalendarClient(
        db=None,
        organization_id="org",
        access_token="tok",
        refresh_token="rt",
        client_id="cid",
        client_secret="cs",
    )
    result = client.create_event(
        "Demo", "2026-08-01T10:00:00Z", "2026-08-01T11:00:00Z",
        attendees=["a@b.com"], description="d",
    )
    assert result == {"event_id": "ev1", "html_link": "https://calendar.google.com/ev1"}
    method, url, payload = calls[0]
    assert method == "POST" and url == EVENTS_URL
    assert payload["attendees"] == [{"email": "a@b.com"}]


def test_refresh_then_retry_success(monkeypatch, db):
    from app.integrations.google_calendar.client import GoogleCalendarClient
    from app.models.integration import Integration
    from app.utils.encryption import decrypt_value, encrypt_value

    org = _org(db)
    db.add(
        Integration(
            organization_id=org.id,
            provider="google-calendar",
            connected=True,
            access_token=encrypt_value("old_access"),
            refresh_token=encrypt_value("old_refresh"),
        )
    )
    db.commit()

    responses = [
        FakeResp(401, text="invalid_grant"),
        FakeResp(200, {"id": "ev2", "htmlLink": "https://calendar.google.com/ev2"}),
    ]

    def fake_request(method, url, **kwargs):
        return responses.pop(0)

    def fake_post(url, **kwargs):
        assert url == "https://oauth2.googleapis.com/token"
        assert kwargs["data"]["grant_type"] == "refresh_token"
        return FakeResp(200, {"access_token": "new_access", "refresh_token": "new_refresh"})

    monkeypatch.setattr(
        "app.integrations.google_calendar.client.httpx.request", fake_request
    )
    monkeypatch.setattr(
        "app.integrations.google_calendar.client.httpx.post", fake_post
    )

    try:
        client = GoogleCalendarClient(
            db=db,
            organization_id=org.id,
            access_token="old_access",
            refresh_token="old_refresh",
            client_id="cid",
            client_secret="cs",
        )
        result = client.create_event("T", "2026-08-01T10:00:00Z", "2026-08-01T11:00:00Z")
        assert result["event_id"] == "ev2"
        assert client._access_token == "new_access"
        row = (
            db.query(Integration)
            .filter(
                Integration.organization_id == org.id,
                Integration.provider == "google-calendar",
            )
            .first()
        )
        assert decrypt_value(row.access_token) == "new_access"
        assert decrypt_value(row.refresh_token) == "new_refresh"
    finally:
        _teardown(db, org)


def test_refresh_failure_raises_auth_error(monkeypatch):
    from app.integrations.google_calendar.client import (
        GoogleCalendarClient,
        IntegrationAuthError,
    )

    def fake_request(method, url, **kwargs):
        return FakeResp(401, text="expired")

    def fake_post(url, **kwargs):
        return FakeResp(400, text="bad grant")

    monkeypatch.setattr(
        "app.integrations.google_calendar.client.httpx.request", fake_request
    )
    monkeypatch.setattr(
        "app.integrations.google_calendar.client.httpx.post", fake_post
    )

    client = GoogleCalendarClient(
        db=None,
        organization_id="org",
        access_token="tok",
        refresh_token="rt",
        client_id="cid",
        client_secret="cs",
    )
    with pytest.raises(IntegrationAuthError):
        client.create_event("T", "2026-08-01T10:00:00Z", "2026-08-01T11:00:00Z")


def test_list_upcoming_events_success(monkeypatch):
    from app.integrations.google_calendar.client import GoogleCalendarClient

    def fake_request(method, url, **kwargs):
        assert kwargs["params"]["singleEvents"] == "true"
        return FakeResp(
            200,
            {"items": [{"id": "e1", "htmlLink": "https://l", "summary": "s"}]},
        )

    monkeypatch.setattr(
        "app.integrations.google_calendar.client.httpx.request", fake_request
    )
    client = GoogleCalendarClient(
        db=None, organization_id="org", access_token="tok", refresh_token="rt"
    )
    result = client.list_upcoming_events(max_results=5)
    assert result == [{"event_id": "e1", "html_link": "https://l", "summary": "s"}]


def test_not_connected_raises():
    from app.integrations.google_calendar.client import IntegrationNotConnectedError
    from app.integrations.google_calendar.service import get_client

    with pytest.raises(IntegrationNotConnectedError):
        get_client(_FakeDB(), "org")


@pytest.mark.db
def test_create_meeting_succeeds_without_calendar(db):
    """Scheduling must never hard-fail when Calendar isn't connected."""
    from app.ai.tools.task_tools import TASK_TOOLS
    from app.models.meeting import Meeting

    org = _org(db)
    try:
        result = TASK_TOOLS["create_meeting"].handler(
            db,
            org.id,
            None,
            {
                "title": "Sell the deal",
                "start_time": "2026-08-01T10:00:00Z",
                "end_time": "2026-08-01T11:00:00Z",
                "participants": ["client@co.com"],
            },
        )
        assert result["created"] is True
        assert result["calendar_synced"] is False
        assert "error" not in result
        row = (
            db.query(Meeting)
            .filter(Meeting.organization_id == org.id)
            .first()
        )
        assert row is not None
        assert row.external_event_id is None
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_create_meeting_syncs_when_connected(db, monkeypatch):
    from app.ai.tools import TASK_TOOLS
    from app.models.integration import Integration
    from app.models.meeting import Meeting

    org = _org(db)
    db.add(
        Integration(
            organization_id=org.id,
            provider="google-calendar",
            connected=True,
            access_token="tok",
            refresh_token="rt",
        )
    )
    db.commit()

    def fake_request(method, url, **kwargs):
        return FakeResp(
            200,
            {"id": "evX", "htmlLink": "https://calendar.google.com/evX"},
        )

    monkeypatch.setattr(
        "app.integrations.google_calendar.client.httpx.request", fake_request
    )

    try:
        result = TASK_TOOLS["create_meeting"].handler(
            db,
            org.id,
            None,
            {
                "title": "Call with Acme",
                "start_time": "2026-08-01T10:00:00Z",
                "end_time": "2026-08-01T11:00:00Z",
                "participants": ["acme@co.com"],
            },
        )
        assert result["created"] is True
        assert result["calendar_synced"] is True
        assert result["external_event_id"] == "evX"
        assert result["html_link"] == "https://calendar.google.com/evX"
        row = (
            db.query(Meeting)
            .filter(Meeting.organization_id == org.id)
            .first()
        )
        assert row.external_event_id == "evX"
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_create_meeting_sync_failure_still_succeeds(db, monkeypatch):
    """A Calendar API error must not break internal scheduling."""
    from app.ai.tools import TASK_TOOLS
    from app.models.integration import Integration
    from app.models.meeting import Meeting

    org = _org(db)
    db.add(
        Integration(
            organization_id=org.id,
            provider="google-calendar",
            connected=True,
            access_token="tok",
            refresh_token="rt",
        )
    )
    db.commit()

    def fake_request(method, url, **kwargs):
        return FakeResp(500, text="boom")

    monkeypatch.setattr(
        "app.integrations.google_calendar.client.httpx.request", fake_request
    )

    try:
        result = TASK_TOOLS["create_meeting"].handler(
            db,
            org.id,
            None,
            {
                "title": "Meeting that calendar drops",
                "start_time": "2026-08-01T10:00:00Z",
                "end_time": "2026-08-01T11:00:00Z",
            },
        )
        assert result["created"] is True
        assert result["calendar_synced"] is False
        row = (
            db.query(Meeting)
            .filter(Meeting.organization_id == org.id)
            .first()
        )
        assert row is not None
        assert row.external_event_id is None
    finally:
        _teardown(db, org)


def test_meeting_tools_registered_and_allowlisted():
    """Lock down the registered-tool-but-missing-from-allowlist bug class."""
    from app.ai.guardrails import _SAFE_TOOL_NAMES, validate_tool_call
    from app.ai.tools import ALL_TOOLS, get_tool

    for name in ("create_meeting", "list_meetings"):
        assert name in ALL_TOOLS
        assert get_tool(name) is not None
        assert name in _SAFE_TOOL_NAMES
        assert validate_tool_call(name, {})