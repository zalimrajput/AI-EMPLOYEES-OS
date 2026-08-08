"""Hosted meeting-audio transcription (OpenAI Whisper STT).

Architectural choice: a **hosted** transcription API is used instead of a
local Whisper model — nothing (ffmpeg, model weights) runs at the OS level.
Audio is streamed as a multipart upload straight to OpenAI's
``/audio/transcriptions`` endpoint via httpx, mirroring the direct-httpx
style used by the Gmail / Google Calendar integrations rather than adding a
new SDK.

Error handling mirrors the integration conventions
(``IntegrationNotConnectedError`` / ``IntegrationAuthError`` in the Stripe
and Gmail clients): a ``TranscriptionNotConfiguredError`` when no key is
present, ``TranscriptionError`` for every API failure.
"""
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("app.integrations.transcription")

TRANSCRIPTIONS_URL = "https://api.openai.com/v1/audio/transcriptions"
TRANSCRIBE_MODEL = "whisper-1"
_DEFAULT_MIME = "audio/mpeg"


class TranscriptionNotConfiguredError(Exception):
    """Raised when no OpenAI API key is configured for transcription."""

    def __init__(self, message: str | None = None):
        super().__init__(
            message
            or "Transcription isn't configured — set OPENAI_API_KEY in Settings first."
        )


class TranscriptionError(Exception):
    """Raised when the hosted transcription API fails or rejects the request."""


def _api_key() -> str:
    key = getattr(settings, "OPENAI_API_KEY", None)
    if not key or not str(key).strip():
        raise TranscriptionNotConfiguredError()
    return str(key)


def transcribe_audio(
    audio_bytes: bytes,
    filename: str,
    mime_type: str | None = None,
) -> dict:
    """Transcribe one audio payload via a hosted STT API.

    Returns ``{"text": str, "duration_seconds": float | None}``. Raises
    ``TranscriptionNotConfiguredError`` when no key is configured and
    ``TranscriptionError`` for API/transport failures.
    """
    key = _api_key()
    safe_name = filename or "recording.mp3"
    files = {
        "file": (
            safe_name,
            audio_bytes,
            mime_type or _DEFAULT_MIME,
        )
    }
    data = {"model": TRANSCRIBE_MODEL, "response_format": "verbose_json"}
    try:
        response = httpx.post(
            TRANSCRIPTIONS_URL,
            headers={"Authorization": f"Bearer {key}"},
            files=files,
            data=data,
            timeout=120.0,
        )
    except httpx.HTTPError as exc:
        raise TranscriptionError(f"Transcription request failed: {exc}") from exc

    if response.status_code >= 400:
        raise TranscriptionError(
            f"Transcription API error {response.status_code}: "
            f"{response.text[:500]}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise TranscriptionError("Transcription API returned invalid JSON") from exc

    text = str(payload.get("text", "")).strip()
    duration = payload.get("duration")
    return {
        "text": text,
        "duration_seconds": float(duration) if duration is not None else None,
    }