from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class AIMessage(Base):

    __tablename__ = "ai_messages"


    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )


    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True
    )


    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False
    )


    role = Column(
        String,
        nullable=False
    )


    message = Column(
        Text,
        nullable=False
    )


    tool_calls = Column(
        JSON,
        nullable=True
    )


    # database column remains "metadata"
    # python attribute is message_metadata
    message_metadata = Column(
        "metadata",
        JSON,
        nullable=True
    )


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )