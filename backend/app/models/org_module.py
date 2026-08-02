import uuid

from sqlalchemy import (
    Column,
    Boolean,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class OrgModule(Base):

    __tablename__ = "org_modules"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    module_key = Column(
        String,
        nullable=False
    )

    enabled_by_super_admin = Column(
        Boolean,
        default=True
    )

    enabled_by_org_admin = Column(
        Boolean,
        default=True
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
