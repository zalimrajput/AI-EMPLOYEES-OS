"""AI message persistence used by the chat API and streaming engine."""
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_message import AIMessage


def add_message(
    db: Session,
    organization_id,
    conversation_id,
    role: str,
    message: str,
    tool_calls: Any = None,
    metadata: Any = None,
) -> AIMessage:
    row = AIMessage(
        organization_id=organization_id,
        conversation_id=conversation_id,
        role=role,
        message=message,
        tool_calls=tool_calls,
        metadata=metadata,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_messages(db: Session, conversation_id) -> list[AIMessage]:
    return (
        db.query(AIMessage)
        .filter(AIMessage.conversation_id == conversation_id)
        .order_by(AIMessage.created_at)
        .all()
    )