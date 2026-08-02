import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from sqlalchemy.sql import func

from app.models.base import Base


class Quotation(Base):

    __tablename__ = "quotations"

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

    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id"),
        nullable=True
    )

    quotation_number = Column(Text)
    status = Column(Text, default="draft")

    subtotal = Column(NUMERIC(12, 2))
    tax = Column(NUMERIC(12, 2))
    discount = Column(NUMERIC(12, 2))
    total = Column(NUMERIC(12, 2))
    pdf_url = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class QuotationItem(Base):

    __tablename__ = "quotation_items"

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

    quotation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True
    )

    description = Column(Text)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(NUMERIC(12, 2), nullable=False, default=0)
    tax_rate = Column(NUMERIC(5, 2), default=0)
    discount = Column(NUMERIC(12, 2), default=0)
    line_total = Column(NUMERIC(12, 2), nullable=False, default=0)
    sort_order = Column(Integer, default=0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
