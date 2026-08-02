import uuid

from sqlalchemy import (
    Column,
    Text,
    BigInteger,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.models.base import Base


class StorageFile(Base):

    __tablename__ = "storage_files"

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

    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    file_name = Column(
        Text,
        nullable=False
    )
    file_path = Column(
        Text,
        nullable=False
    )
    bucket = Column(Text, default="documents")
    mime_type = Column(Text)
    file_size = Column(BigInteger, default=0)
    storage_provider = Column(Text, default="supabase")
    url = Column(Text)
    entity_type = Column(Text)
    entity_id = Column(UUID(as_uuid=True))
    metadata_json = Column("metadata", JSONB, default={})

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class StorageQuota(Base):

    __tablename__ = "storage_quotas"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    max_storage_bytes = Column(BigInteger, default=1073741824)
    used_storage_bytes = Column(BigInteger, default=0)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class FileAccessPermission(Base):

    __tablename__ = "file_access_permissions"

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

    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("storage_files.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )

    permission = Column(Text, default="read")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
