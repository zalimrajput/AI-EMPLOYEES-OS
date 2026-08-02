import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class Module(Base):

    __tablename__ = "modules"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    key = Column(
        String,
        nullable=False,
        unique=True
    )

    name = Column(
        String,
        nullable=False
    )

    description = Column(
        Text
    )

    icon = Column(
        String,
        default="Box"
    )

    group_name = Column(
        String,
        default="operations"
    )

    sort_order = Column(
        Integer,
        default=0
    )

    dashboard = Column(
        String
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
