import uuid

from sqlalchemy import (
    Column,
    Text,
    Integer,
    BigInteger,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
from sqlalchemy.sql import func

from app.models.base import Base


class UsageRecord(Base):

    __tablename__ = "usage_records"

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

    ai_employee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_employees.id", ondelete="SET NULL"),
        nullable=True
    )

    usage_type = Column(
        Text,
        nullable=False
    )
    provider = Column(Text)
    model = Column(Text)
    quantity = Column(NUMERIC, default=1)
    tokens_used = Column(Integer, default=0)
    metadata_json = Column("metadata", JSONB, default={})

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class StorageUsage(Base):

    __tablename__ = "storage_usage"

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

    storage_type = Column(Text)
    file_count = Column(Integer, default=0)
    storage_bytes = Column(BigInteger, default=0)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class APIUsage(Base):

    __tablename__ = "api_usage"

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

    endpoint = Column(Text)
    request_count = Column(Integer, default=1)
    response_status = Column(Integer)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
