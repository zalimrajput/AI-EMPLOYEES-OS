from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_message import AIMessage


class AIMessageRepository:
    model = AIMessage

    def __init__(self, db: Session, organization_id) -> None:
        self.db = db
        self.organization_id = organization_id

    def create(
        self,
        conversation_id,
        role: str,
        message: str,
        tool_calls: Any = None,
        metadata: Any = None,
    ) -> AIMessage:
        row = AIMessage(
            organization_id=self.organization_id,
            conversation_id=conversation_id,
            role=role,
            message=message,
            tool_calls=tool_calls,
            metadata=metadata,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_for_conversation(self, conversation_id) -> list[AIMessage]:
        return (
            self.db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at)
            .all()
        )