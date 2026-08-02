import uuid

from sqlalchemy import (
    Column,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.models.base import Base


class Activity(Base):

    __tablename__ = "activities"

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
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    entity_type = Column(Text)
    entity_id = Column(UUID(as_uuid=True))

    action = Column(
        Text,
        nullable=False
    )
    metadata_json = Column("metadata", JSONB, default={})

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
