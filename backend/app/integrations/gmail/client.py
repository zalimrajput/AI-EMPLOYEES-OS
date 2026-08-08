"""Gmail REST API client built on the stored OAuth credentials.

Tokens are stored encrypted (``app.utils.encryption``) by
``app.services.integration_service.save_credentials``; this client decrypts
them via ``decrypt_value`` and talks to the Gmail API directly with httpx.
On a 401 the stored refresh_token is exchanged for a new access_token, the
encrypted row is updated, and the request is retried once.
"""

import base64
from email.message import EmailMessage

import httpx

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
GMAIL_SEND_URL = f"{GMAIL_API}/messages/send"
GMAIL_LIST_URL = f"{GMAIL_API}/messages"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"


class IntegrationNotConnectedError(Exception):
    """Raised when the org has no connected Gmail integration."""


class IntegrationAuthError(Exception):
    """Raised when Gmail rejects/refreshes fail and we cannot authenticate."""


def _header_value(value) -> str | None:
    """Normalize a to/cc/bcc value (comma string or list) to a header string."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


class GmailClient:
    """Minimal Gmail API client with automatic token refresh."""

    def __init__(
        self,
        *,
        db,
        organization_id,
        access_token: str | None,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_url: str = OAUTH_TOKEN_URL,
    ):
        self._db = db
        self._organization_id = organization_id
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url

    # -- internal helpers -------------------------------------------------

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}

    def _refresh(self) -> None:
        """Exchange the refresh token for a new access token and persist it."""
        if not (self._refresh_token and self._client_id and self._client_secret):
            raise IntegrationAuthError(
                "Gmail access token expired and no refresh credentials are available"
            )
        resp = httpx.post(
            self._token_url,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": self._refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        if resp.status_code >= 300:
            raise IntegrationAuthError(
                f"Gmail token refresh failed: {resp.status_code} {resp.text[:200]}"
            )
        payload = resp.json()
        new_access = payload.get("access_token")
        if not new_access:
            raise IntegrationAuthError(
                "Gmail token refresh returned no access_token"
            )
        self._access_token = new_access
        if payload.get("refresh_token"):
            self._refresh_token = payload["refresh_token"]
        self._persist(new_access, payload.get("refresh_token"))

    def _persist(self, access_token: str, refresh_token: str | None) -> None:
        """Re-encrypt and store the refreshed tokens in the integrations table."""
        from app.services.integration_service import save_credentials

        tokens = {"access_token": access_token}
        if refresh_token:
            tokens["refresh_token"] = refresh_token
        save_credentials(self._db, self._organization_id, "gmail", tokens)

    def _request(self, method: str, url: str, *, params=None, json=None) -> httpx.Response:
        """One request, with a single 401-refresh-retry round."""
        resp = httpx.request(
            method,
            url,
            headers=self._headers(),
            params=params,
            json=json,
            timeout=30,
        )
        if resp.status_code == 401:
            self._refresh()
            resp = httpx.request(
                method,
                url,
                headers=self._headers(),
                params=params,
                json=json,
                timeout=30,
            )
        return resp

    # -- public API -------------------------------------------------------

    def send_email(
        self,
        to,
        subject: str,
        body: str,
        cc=None,
        bcc=None,
        attachments=None,
    ) -> dict:
        """Send an RFC 2822 message through the user's Gmail account.

        ``attachments`` is an optional list of ``{"filename", "content_bytes",
        "mime_type"}``. When present the message becomes multipart/mixed;
        when empty/None the plain-text path is unchanged.
        """
        msg = EmailMessage()
        msg["to"] = _header_value(to)
        msg["subject"] = subject
        cc_header = _header_value(cc)
        bcc_header = _header_value(bcc)
        if cc_header:
            msg["cc"] = cc_header
        if bcc_header:
            msg["bcc"] = bcc_header
        msg.set_content(body or "")

        for attachment in attachments or []:
            data = attachment.get("content_bytes")
            if isinstance(data, str):
                data = data.encode("utf-8")
            mime = attachment.get("mime_type") or "application/octet-stream"
            maintype, _, subtype = mime.partition("/")
            msg.add_attachment(
                data,
                maintype=maintype or "application",
                subtype=subtype or "octet-stream",
                filename=attachment.get("filename"),
            )

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
        resp = self._request("POST", GMAIL_SEND_URL, json={"raw": raw})
        if resp.status_code >= 300:
            raise RuntimeError(f"Gmail send failed: {resp.status_code} {resp.text[:200]}")
        payload = resp.json()
        return {
            "id": payload.get("id"),
            "thread_id": payload.get("threadId"),
            "status": "sent",
        }

    def list_recent_messages(self, query: str | None = None, max_results: int = 10) -> list[dict]:
        """Return the most recent message ids, optionally filtered by query."""
        params = {"maxResults": int(max_results)}
        if query:
            params["q"] = query
        resp = self._request("GET", GMAIL_LIST_URL, params=params)
        if resp.status_code >= 300:
            raise RuntimeError(f"Gmail list failed: {resp.status_code} {resp.text[:200]}")
        payload = resp.json()
        return [
            {"id": m.get("id"), "thread_id": m.get("threadId")}
            for m in payload.get("messages", [])
        ]
