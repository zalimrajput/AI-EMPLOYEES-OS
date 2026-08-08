"""transcribe_meeting_audio tool tests.

All tests mock httpx — no real API is ever hit. The hosted STT client is
exercised through its documented interface; the success path uses the real
DB and reads the persisted meeting fresh.
"""
import sys
import uuid

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text

from app.ai.tools.task_tools import TASK_TOOLS


def _org(db):
    from app.models.organization import Organization

    org = Organization(
        name="Transcribe Org",
        slug=f"ts-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _teardown(db, org):
    deletes = [
        "DELETE FROM meetings WHERE organization_id = :id",
        "DELETE FROM storage_files WHERE organization_id = :id",
        "DELETE FROM storage_quotas WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _meeting(db, org):
    from app.models.meeting import Meeting

    meeting = Meeting(organization_id=org.id, title="Team sync", participants=[])
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def _audio_file(db, org, path):
    from app.models.storage import StorageFile

    row = StorageFile(
        organization_id=org.id,
        file_name="meeting.mp3",
        file_path=str(path),
        mime_type="audio/mpeg",
        file_size=123,
        bucket="documents",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _fresh_meeting(db, meeting_id):
    from app.models.meeting import Meeting

    return db.get(Meeting, meeting_id)


def _success_response(text="Hello everyone this is the meeting transcript", duration=12.5):
    class _Resp:
        status_code = 200

        def json(self):
            return {"text": text, "duration": duration}

    return _Resp()


def _set_key(monkeypatch, value="sk-test-do-not-use"):
    from app.integrations.transcription import client

    monkeypatch.setattr(client.settings, "OPENAI_API_KEY", value)


@pytest.mark.db
def test_transcribe_success_persists(db, monkeypatch, tmp_path):
    captured = {}

    def fake_post(url, headers, files, data, timeout):
        captured["url"] = url
        captured["auth"] = headers.get("Authorization")
        captured["filename"] = files["file"][0]
        captured["mime"] = files["file"][2]
        captured["model"] = data["model"]
        return _success_response()

    _set_key(monkeypatch, "sk-test-123")
    monkeypatch.setattr(
        "app.integrations.transcription.client.httpx.post", fake_post
    )

    audio_path = tmp_path / "meeting.mp3"
    audio_path.write_bytes(b"\x00fake-audio-bytes")

    org = _org(db)
    m = _meeting(db, org)
    _audio_file(db, org, audio_path)

    try:
        result = TASK_TOOLS["transcribe_meeting_audio"].handler(
            db, org.id, None, {"meeting_id": str(m.id), "audio_url": str(audio_path)}
        )
        assert "error" not in result
        assert result["meeting_id"] == str(m.id)
        assert result["source"] == "audio"
        assert result["duration_seconds"] == 12.5
        assert "meeting transcript" in result["transcript"]

        # persistence: fresh DB read
        fresh = _fresh_meeting(db, m.id)
        assert fresh.transcript == result["transcript"]
        assert fresh.transcript == "Hello everyone this is the meeting transcript"

        # request shape matches the hosted STT contract
        assert captured["url"] == "https://api.openai.com/v1/audio/transcriptions"
        assert captured["auth"] == "Bearer sk-test-123"
        assert captured["filename"] == "meeting.mp3"
        assert captured["mime"] == "audio/mpeg"
        assert captured["model"] == "whisper-1"
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_transcribe_success_appends_to_existing_notes(db, monkeypatch, tmp_path):
    def fake_post(url, headers, files, data, timeout):
        return _success_response(text="Second half of the meeting.")

    _set_key(monkeypatch, "sk-test-123")
    monkeypatch.setattr(
        "app.integrations.transcription.client.httpx.post", fake_post
    )

    audio_path = tmp_path / "meeting.mp3"
    audio_path.write_bytes(b"fake-audio")

    org = _org(db)
    m = _meeting(db, org)
    m.transcript = "First part, typed notes."
    db.add(m)
    db.commit()
    _audio_file(db, org, audio_path)

    try:
        result = TASK_TOOLS["transcribe_meeting_audio"].handler(
            db, org.id, None, {"meeting_id": str(m.id), "audio_url": str(audio_path)}
        )
        assert result["transcript"] == (
            "First part, typed notes.\n\nSecond half of the meeting."
        )
        fresh = _fresh_meeting(db, m.id)
        assert fresh.transcript == result["transcript"]
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_transcribe_not_configured_returns_structured_error(
    db, monkeypatch, tmp_path
):
    def unexpected(*args, **kwargs):
        raise AssertionError("no API call should be made without a key")

    _set_key(monkeypatch, None)
    monkeypatch.setattr(
        "app.integrations.transcription.client.httpx.post", unexpected
    )

    audio_path = tmp_path / "meeting.mp3"
    audio_path.write_bytes(b"fake-audio")

    org = _org(db)
    m = _meeting(db, org)
    _audio_file(db, org, audio_path)

    try:
        result = TASK_TOOLS["transcribe_meeting_audio"].handler(
            db, org.id, None, {"meeting_id": str(m.id), "audio_url": str(audio_path)}
        )
        assert "error" in result
        assert "not configured" in result["error"]
        fresh = _fresh_meeting(db, m.id)
        assert fresh.transcript is None
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_transcribe_api_failure_returns_structured_error(
    db, monkeypatch, tmp_path
):
    class _ErrRes:
        status_code = 502
        text = "<html>bad gateway</html>"

        def json(self):
            return {}

    def failing_post(url, headers, files, data, timeout):
        return _ErrRes()

    _set_key(monkeypatch, "sk-test-123")
    monkeypatch.setattr(
        "app.integrations.transcription.client.httpx.post", failing_post
    )

    audio_path = tmp_path / "meeting.mp3"
    audio_path.write_bytes(b"fake-audio")

    org = _org(db)
    m = _meeting(db, org)
    _audio_file(db, org, audio_path)

    try:
        result = TASK_TOOLS["transcribe_meeting_audio"].handler(
            db, org.id, None, {"meeting_id": str(m.id), "audio_url": str(audio_path)}
        )
        assert "error" in result
        assert "Transcription failed" in result["error"]
        fresh = _fresh_meeting(db, m.id)
        assert fresh.transcript is None
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_transcribe_meeting_not_found_before_api_call(db, monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("no API call for an unknown meeting")

    _set_key(monkeypatch, None)
    monkeypatch.setattr(
        "app.integrations.transcription.client.httpx.post", unexpected
    )

    org = _org(db)
    try:
        result = TASK_TOOLS["transcribe_meeting_audio"].handler(
            db,
            org.id,
            None,
            {"meeting_id": str(uuid.uuid4()), "audio_url": "/documents/missing.mp3"},
        )
        assert result == {"error": "Meeting not found"}
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_transcribe_missing_audio_file_returns_error(db, monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("API must not be called when audio is missing")

    _set_key(monkeypatch, None)
    monkeypatch.setattr(
        "app.integrations.transcription.client.httpx.post", unexpected
    )

    org = _org(db)
    m = _meeting(db, org)
    try:
        result = TASK_TOOLS["transcribe_meeting_audio"].handler(
            db,
            org.id,
            None,
            {"meeting_id": str(m.id), "audio_url": "/documents/not-uploaded.mp3"},
        )
        assert "error" in result
        assert "Audio file not found" in result["error"]
    finally:
        _teardown(db, org)


def test_transcribe_tool_registered_and_guarded():
    from app.ai.agents.executive_agent import AGENT as EXECUTIVE
    from app.ai.agents.recruiter_agent import AGENT as RECRUITER
    from app.ai.agents.sales_agent import AGENT as SALES
    from app.ai.guardrails import _SAFE_TOOL_NAMES
    from app.ai.tools import ALL_TOOLS

    assert "transcribe_meeting_audio" in ALL_TOOLS
    assert "transcribe_meeting_audio" in _SAFE_TOOL_NAMES
    for agent in (EXECUTIVE, RECRUITER, SALES):
        assert "transcribe_meeting_audio" in agent.allowed_tools