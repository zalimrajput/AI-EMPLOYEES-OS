from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
    message: str


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

    user_message = AIMessage(
        organization_id=me.organization_id,
        conversation_id=conversation.id,
        role="user",
        message=data.message,
    )
    db.add(user_message)

    # Placeholder AI reply (no LLM key wired into this endpoint yet).
    employee_name = "AI Employee"
    if conversation.ai_employee_id is not None:
        employee = db.query(AIEmployee).filter(
            AIEmployee.id == conversation.ai_employee_id
        ).first()
        if employee is not None:
            employee_name = employee.name

    reply = AIMessage(
        organization_id=me.organization_id,
        conversation_id=conversation.id,
        role="assistant",
        message=(
            f"Thanks — I'm {employee_name} and I've received your request: "
            f"\"{data.message}\". Your message is stored in this conversation."
        ),
        metadata={"pending": True},
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply
