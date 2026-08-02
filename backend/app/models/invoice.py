import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    Date,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from sqlalchemy.sql import func

from app.models.base import Base


class Invoice(Base):

    __tablename__ = "invoices"

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

    invoice_number = Column(Text)
    amount = Column(NUMERIC(12, 2))
    status = Column(Text, default="unpaid")
    due_date = Column(Date)
    pdf_url = Column(Text)

    # 0047_invoice_extensions
    recurrence_interval = Column(Integer)
    recurrence_period = Column(Text)
    next_billing_date = Column(Date)
    payment_link_url = Column(Text)
    qr_code_url = Column(Text)
    ai_summary = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class InvoiceItem(Base):

    __tablename__ = "invoice_items"

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
        ForeignKey("invoices.id", ondelete="CASCADE"),
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
