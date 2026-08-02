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


class Payment(Base):

    __tablename__ = "payments"

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

    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=True
    )

    amount = Column(NUMERIC(12, 2))
    payment_method = Column(Text)
    paid_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
