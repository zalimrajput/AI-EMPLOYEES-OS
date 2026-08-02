import uuid

from sqlalchemy import (
    Column,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class Reminder(Base):

    __tablename__ = "reminders"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )

    target_type = Column(Text)
    target_id = Column(UUID(as_uuid=True))

    remind_at = Column(
        DateTime(timezone=True),
        nullable=False
    )
    message = Column(Text)
    channel = Column(Text, default="email")
    triggered = Column(Boolean, default=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
