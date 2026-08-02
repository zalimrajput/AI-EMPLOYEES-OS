import uuid

from sqlalchemy import (
    Column,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from sqlalchemy.sql import func

from app.models.base import Base


class Product(Base):

    __tablename__ = "products"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=True
    )

    name = Column(Text)
    description = Column(Text)
    price = Column(NUMERIC(12, 2))
    tax_rate = Column(NUMERIC, default=0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
