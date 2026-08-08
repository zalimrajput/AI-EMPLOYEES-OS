"""Third-party integrations: OAuth connect/disconnect + Stripe webhook.

All tokens are encrypted at rest via ``app.utils.encryption``.  The frontend
settings page lists integrations and shows Connected/Connect state from the
``integrations`` table.
"""
import logging
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.models.integration import Integration
from app.utils.encryption import encrypt_value

logger = logging.getLogger("app.services.integration_service")

# provider key -> (client id setting, client secret setting, redirect setting)
_PROVIDER_CONFIG = {
    "gmail": (
        "GMAIL_CLIENT_ID",
        "GMAIL_CLIENT_SECRET",
        "GMAIL_REDIRECT_URI",
        "https://accounts.google.com/o/oauth2/v2/auth",
        "https://oauth2.googleapis.com/token",
        "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly",
    ),
    "google-calendar": (
        "GOOGLE_CAL_CLIENT_ID",
        "GOOGLE_CAL_CLIENT_SECRET",
        "GOOGLE_CAL_REDIRECT_URI",
        "https://accounts.google.com/o/oauth2/v2/auth",
        "https://oauth2.googleapis.com/token",
        "https://www.googleapis.com/auth/calendar.events",
    ),
    "slack": (
        "SLACK_CLIENT_ID",
        "SLACK_CLIENT_SECRET",
        "SLACK_REDIRECT_URI",
        "https://slack.com/oauth/v2/authorize",
        "https://slack.com/api/oauth.v2.access",
        "channels:read chat:write",
    ),
    "outlook": (
        "OUTLOOK_CLIENT_ID",
        "OUTLOOK_CLIENT_SECRET",
        "OUTLOOK_REDIRECT_URI",
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "Mail.Read Mail.Send",
    ),
    "microsoft365": (
        "MICROSOFT_CLIENT_ID",
        "MICROSOFT_CLIENT_SECRET",
        "MICROSOFT_REDIRECT_URI",
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "Calendars.ReadWrite Mail.ReadWrite Tasks.ReadWrite",
    ),
}


def get_provider_config(provider: str) -> dict | None:
    cfg = _PROVIDER_CONFIG.get(provider)
    if cfg is None:
        return None
    cid, secret, redirect, auth_url, token_url, scope = cfg
    if not getattr(settings, cid, None):
        return None
    return {
        "client_id": getattr(settings, cid),
        "client_secret": getattr(settings, secret),
        "redirect_uri": getattr(settings, redirect),
        "auth_url": auth_url,
        "token_url": token_url,
        "scope": scope,
    }


def build_authorize_url(provider: str, state: str) -> str:
    cfg = get_provider_config(provider)
    if cfg is None:
        raise ValueError("provider not configured")
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "scope": cfg["scope"],
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{cfg['auth_url']}?{urlencode(params)}"


async def exchange_code(provider: str, code: str) -> dict:
    cfg = get_provider_config(provider)
    if cfg is None:
        raise ValueError("provider not configured")
    data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "redirect_uri": cfg["redirect_uri"],
        "grant_type": "authorization_code",
        "code": code,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(cfg["token_url"], data=data)
    if resp.status_code >= 300:
        raise RuntimeError(f"token exchange failed: {resp.status_code} {resp.text[:200]}")
    return resp.json()


def save_credentials(
    db,
    organization_id,
    provider: str,
    tokens: dict,
    metadata: dict | None = None,
) -> Integration:
    """Upsert encrypted credentials for an org/provider pair."""
    row = (
        db.query(Integration)
        .filter(
            Integration.organization_id == organization_id,
            Integration.provider == provider,
        )
        .first()
    )
    if row is None:
        row = Integration(
            organization_id=organization_id,
            provider=provider,
            connected=True,
        )
        db.add(row)

    row.access_token = encrypt_value(tokens.get("access_token"))
    row.refresh_token = encrypt_value(tokens.get("refresh_token"))
    if metadata:
        row.metadata_json = {**(row.metadata_json or {}), **metadata}
    row.connected = True
    db.commit()
    db.refresh(row)
    return row


def disconnect(db, integration: Integration) -> Integration:
    integration.connected = False
    db.commit()
    db.refresh(integration)
    return integration