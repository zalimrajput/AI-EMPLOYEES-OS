import uuid

from sqlalchemy import (
    Column,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func

from app.models.base import Base


class UserSession(Base):

    __tablename__ = "user_sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True
    )

    session_token = Column(
        Text,
        nullable=False
    )
    ip_address = Column(INET)
    user_agent = Column(Text)
    device_name = Column(Text)
    last_activity = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    expires_at = Column(DateTime(timezone=True))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class MFASetting(Base):

    __tablename__ = "mfa_settings"

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

    method = Column(
        Text,
        nullable=False
    )
    secret = Column(Text)
    enabled = Column(Boolean, default=False)
    backup_codes = Column(JSONB, default=[])

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class SSOConnection(Base):

    __tablename__ = "sso_connections"

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

    provider = Column(
        Text,
        nullable=False
    )
    provider_domain = Column(Text)
    client_id = Column(Text)
    client_secret = Column(Text)
    metadata_json = Column("metadata", JSONB, default={})
    enabled = Column(Boolean, default=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class SecurityEvent(Base):

    __tablename__ = "security_events"

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

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    event_type = Column(
        Text,
        nullable=False
    )
    ip_address = Column(INET)
    metadata_json = Column("metadata", JSONB, default={})

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
