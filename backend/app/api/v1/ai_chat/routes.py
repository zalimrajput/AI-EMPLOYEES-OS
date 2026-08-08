from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.guardrails import is_flagged, refuse_reply, sanitize_input
from app.ai.orchestrator import execute_turn
from app.ai.memory import remember
from app.api.v1._crud import require_org_member
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.ai_conversation import AIConversation
from app.models.ai_employee import AIEmployee
from app.models.ai_message import AIMessage


router = APIRouter(
    prefix="/ai-chat",
    tags=["AI Chat"]
)


class ConversationCreate(BaseModel):
    ai_employee_id: UUID | None = None
    title: str | None = None


class MessageCreate(BaseModel):
    conversation_id: UUID
    content: str | None = None
    message: str | None = None

    def text(self) -> str:
        return self.content or self.message or ""


class ConversationOut(BaseModel):
    id: UUID
    ai_employee_id: UUID | None
    title: str | None
    status: str | None

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    message: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class VoiceMessageOut(MessageOut):
    """Assistant reply plus the transcribed text so the caller can verify it."""

    transcribed_text: str | None = None


@router.get("/conversations", response_model=list[ConversationOut])
# Protected endpoint: lists the caller's organization AI conversations.
def list_conversations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    return (
        db.query(AIConversation)
        .filter(AIConversation.organization_id == me.organization_id)
        .order_by(AIConversation.created_at.desc())
        .all()
    )


@router.post("/conversations", response_model=ConversationOut, status_code=201)
# Protected endpoint: creates an AI conversation inside the caller's org.
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    if data.ai_employee_id is not None:
        employee = db.query(AIEmployee).filter(
            AIEmployee.id == data.ai_employee_id,
            AIEmployee.organization_id == me.organization_id,
        ).first()
        if employee is None:
            raise HTTPException(status_code=404, detail="AI employee not found")
    conversation = AIConversation(
        organization_id=me.organization_id,
        user_id=me.id,
        ai_employee_id=data.ai_employee_id,
        title=data.title or "New conversation",
        status="active",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
# Protected endpoint: lists the messages of one org-scoped conversation.
def list_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    conversation = db.query(AIConversation).filter(
        AIConversation.id == conversation_id,
        AIConversation.organization_id == me.organization_id,
    ).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return (
        db.query(AIMessage)
        .filter(AIMessage.conversation_id == conversation_id)
        .order_by(AIMessage.created_at)
        .all()
    )


@router.post("/messages", response_model=MessageOut, status_code=201)
# Protected endpoint: sends a message; stores the user message and a reply.
def send_message(
    data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    conversation = db.query(AIConversation).filter(
        AIConversation.id == data.conversation_id,
        AIConversation.organization_id == me.organization_id,
    ).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    text = sanitize_input(data.text())
    if text is None:
        raise HTTPException(status_code=422, detail="Message must be 1-16000 chars")

    employee = None
    if conversation.ai_employee_id is not None:
        employee = db.query(AIEmployee).filter(
            AIEmployee.id == conversation.ai_employee_id,
            AIEmployee.organization_id == me.organization_id,
        ).first()

    user_message = AIMessage(
        organization_id=me.organization_id,
        conversation_id=conversation.id,
        role="user",
        message=text,
    )
    db.add(user_message)

    if is_flagged(text):
        reply_text = refuse_reply()
    else:
        history = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation.id)
            .order_by(AIMessage.created_at)
            .limit(20)
            .all()
        )
        reply_text, _agent_key = execute_turn(
            db,
            me.organization_id,
            str(me.id),
            conversation,
            text,
            employee=employee,
            history_messages=history,
        )
        if employee is not None:
            remember(
                db, me.organization_id, str(employee.id), f"{text} -> {reply_text}"
            )

    reply = AIMessage(
        organization_id=me.organization_id,
        conversation_id=conversation.id,
        role="assistant",
        message=reply_text,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


def _complete_turn(db, me, conversation, text, *, source: str = "text"):
    """Run the shared user->assistant turn when the message already has text.

    Mirrors the send_message body so voice and text messages follow the exact
    same orchestration path; only the user message's origin marker differs.
    """
    employee = None
    if conversation.ai_employee_id is not None:
        employee = db.query(AIEmployee).filter(
            AIEmployee.id == conversation.ai_employee_id,
            AIEmployee.organization_id == me.organization_id,
        ).first()

    user_message = AIMessage(
        organization_id=me.organization_id,
        conversation_id=conversation.id,
        role="user",
        message=text,
    )
    if source == "voice":
        user_message.message_metadata = {"source": "voice"}
    db.add(user_message)

    if is_flagged(text):
        reply_text = refuse_reply()
    else:
        history = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation.id)
            .order_by(AIMessage.created_at)
            .limit(20)
            .all()
        )
        reply_text, _agent_key = execute_turn(
            db,
            me.organization_id,
            str(me.id),
            conversation,
            text,
            employee=employee,
            history_messages=history,
        )
        if employee is not None:
            remember(
                db, me.organization_id, str(employee.id), f"{text} -> {reply_text}"
            )

    reply = AIMessage(
        organization_id=me.organization_id,
        conversation_id=conversation.id,
        role="assistant",
        message=reply_text,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


@router.post("/messages/voice", response_model=VoiceMessageOut, status_code=201)
# Protected endpoint: same chat flow, but the input is a spoken audio file.
def send_voice_message(
    conversation_id: UUID = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    conversation = db.query(AIConversation).filter(
        AIConversation.id == conversation_id,
        AIConversation.organization_id == me.organization_id,
    ).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    audio_bytes = audio.file.read() if audio else b""
    filename = (audio.filename or "voice-recording.webm").rsplit("/", 1)[-1]
    mime_type = audio.content_type or None

    from app.integrations.transcription.client import (
        TranscriptionError,
        TranscriptionNotConfiguredError,
        transcribe_audio,
    )

    try:
        transcription = transcribe_audio(audio_bytes, filename, mime_type)
    except TranscriptionNotConfiguredError:
        raise HTTPException(
            status_code=422,
            detail="Voice input isn't configured — set OPENAI_API_KEY",
        )
    except TranscriptionError as exc:
        raise HTTPException(status_code=422, detail=f"Voice transcription failed: {exc}")

    transcribed = str(transcription.get("text") or "").strip()
    if not transcribed:
        raise HTTPException(status_code=422, detail="No speech recognized in audio")

    text = sanitize_input(transcribed)
    if text is None:
        raise HTTPException(status_code=422, detail="Message must be 1-16000 chars")

    reply = _complete_turn(db, me, conversation, text, source="voice")
    return {
        "id": reply.id,
        "conversation_id": reply.conversation_id,
        "role": reply.role,
        "message": reply.message,
        "created_at": reply.created_at,
        "transcribed_text": transcribed,
    }


@router.get("/conversations/{conversation_id}/stream")
# Protected endpoint: streams assistant output (SSE) for a conversation turn.
def stream_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    conversation = db.query(AIConversation).filter(
        AIConversation.id == conversation_id,
        AIConversation.organization_id == me.organization_id,
    ).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    from fastapi.responses import StreamingResponse

    employee = None
    if conversation.ai_employee_id is not None:
        employee = db.query(AIEmployee).filter(
            AIEmployee.id == conversation.ai_employee_id,
            AIEmployee.organization_id == me.organization_id,
        ).first()

    last_message = (
        db.query(AIMessage)
        .filter(AIMessage.conversation_id == conversation.id)
        .order_by(AIMessage.created_at.desc())
        .first()
    )

    def _emit():
        from app.ai.model_router import stream as model_stream

        model = employee.model if employee else None
        prompt = last_message.message if last_message else "Hello"
        try:
            for chunk in model_stream(
                [{"role": "user", "content": prompt}],
                model=model,
                temperature=0.3,
            ):
                yield chunk
        except Exception as exc:  # noqa: BLE001
            yield f"\n\n[stream error: {exc.__class__.__name__}]"

    return StreamingResponse(_emit(), media_type="text/event-stream")
