"""Lookup helper: resolve a connected Google Calendar integration."""

from app.integrations.google_calendar.client import (
    GoogleCalendarClient,
    IntegrationNotConnectedError,
    OAUTH_TOKEN_URL,
)
from app.models.integration import Integration
from app.utils.encryption import decrypt_value


def get_client(db, organization_id) -> GoogleCalendarClient:
    """Return a GoogleCalendarClient for the org's connected integration.

    Raises ``IntegrationNotConnectedError`` when no connected
    ``google-calendar`` integration row exists for the organization.
    """
    row = (
        db.query(Integration)
        .filter(
            Integration.organization_id == organization_id,
            Integration.provider == "google-calendar",
            Integration.connected.is_(True),
        )
        .first()
    )
    if row is None:
        raise IntegrationNotConnectedError(
            "No connected Google Calendar integration for this organization"
        )

    from app.services.integration_service import get_provider_config

    cfg = get_provider_config("google-calendar") or {}
    return GoogleCalendarClient(
        db=db,
        organization_id=organization_id,
        access_token=decrypt_value(row.access_token),
        refresh_token=decrypt_value(row.refresh_token),
        client_id=cfg.get("client_id"),
        client_secret=cfg.get("client_secret"),
        token_url=cfg.get("token_url") or OAUTH_TOKEN_URL,
    )
