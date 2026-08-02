import uuid

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class Widget(Base):

    __tablename__ = "widgets"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    module_key = Column(
        String,
        ForeignKey(
            "modules.key",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    widget_key = Column(
        String,
        nullable=False
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

    sort_order = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
