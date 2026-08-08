"""WhatsApp Business Cloud API client built on httpx (no SDK).

The Meta Graph API sends messages and exposes media download for a given
Phone Number ID using an app access token.  Tokens are stored encrypted per
organization via ``app.services.integration_service.save_credentials``; this
client decrypts them through ``app.utils.encryption`` when resolved by
``app.integrations.whatsapp.service.get_client``.
"""

import httpx

GRAPH_API_BASE = "https://graph.facebook.com"
DEFAULT_API_VERSION = "v21.0"


class WhatsAppNotConnectedError(Exception):
    """Raised when the org has no connected WhatsApp integration."""


class WhatsAppError(Exception):
    """Raised when the Meta Graph API rejects or fails a request."""


class WhatsAppClient:
    """Minimal WhatsApp Cloud API client for a single phone number ID."""

    def __init__(
        self,
        *,
        api_token: str,
        phone_number_id: str,
        api_version: str = DEFAULT_API_VERSION,
    ):
        self._api_token = api_token
        self._phone_number_id = phone_number_id
        self._base = f"{GRAPH_API_BASE}/{api_version}"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_token}"}

    def _messages_url(self) -> str:
        return f"{self._base}/{self._phone_number_id}/messages"

    def send_text(self, to: str, message: str) -> dict:
        """Send a plain-text WhatsApp message to a phone number."""
        resp = httpx.post(
            self._messages_url(),
            headers=self._headers(),
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message},
            },
            timeout=30,
        )
        if resp.status_code >= 300:
            raise WhatsAppError(
                f"WhatsApp send failed: {resp.status_code} {resp.text[:200]}"
            )
        payload = resp.json()
        message_ids = (payload.get("messages") or [{}])[0]
        return {
            "id": message_ids.get("id"),
            "status": "sent" if message_ids.get("id") else "queued",
        }

    def media_url(self, media_id: str) -> str:
        """GET the media metadata; returns the downloadable URL."""
        resp = httpx.get(
            f"{self._base}/{media_id}",
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code >= 300:
            raise WhatsAppError(
                f"WhatsApp media lookup failed: {resp.status_code} {resp.text[:200]}"
            )
        url = resp.json().get("url")
        if not url:
            raise WhatsAppError("WhatsApp media metadata returned no download URL")
        return url

    def download_media(self, media_id: str) -> bytes:
        """Download a media object (voice note, image) as raw bytes."""
        url = self.media_url(media_id)
        resp = httpx.get(url, headers=self._headers(), timeout=120)
        if resp.status_code >= 300:
            raise WhatsAppError(
                f"WhatsApp media download failed: {resp.status_code} {resp.text[:200]}"
            )
        return resp.content