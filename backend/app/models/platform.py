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


class PlatformRole(Base):

    __tablename__ = "platform_roles"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    role = Column(Text, nullable=False, default="Super Admin")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class PlatformSetting(Base):

    __tablename__ = "platform_settings"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    key = Column(
        Text,
        nullable=False,
        unique=True
    )
    value = Column(JSONB, default={})

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class PlatformLog(Base):

    __tablename__ = "platform_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    action = Column(
        Text,
        nullable=False
    )
    entity = Column(Text)
    metadata_json = Column("metadata", JSONB, default={})

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
