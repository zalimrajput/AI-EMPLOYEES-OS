import uuid

from sqlalchemy import (
    Column,
    Text,
    Date,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
from sqlalchemy.sql import func

from app.models.base import Base


class ExpenseCategory(Base):

    __tablename__ = "expense_categories"

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

    name = Column(
        Text,
        nullable=False
    )
    description = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Expense(Base):

    __tablename__ = "expenses"

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

    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("expense_categories.id", ondelete="SET NULL"),
        nullable=True
    )

    submitted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )

    title = Column(
        Text,
        nullable=False
    )
    description = Column(Text)
    amount = Column(
        NUMERIC(12, 2),
        nullable=False
    )
    currency = Column(Text, default="USD")
    expense_date = Column(Date)
    receipt_url = Column(Text)
    status = Column(Text, default="pending")

    approved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Budget(Base):

    __tablename__ = "budgets"

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

    name = Column(Text)
    amount = Column(NUMERIC(12, 2))
    period = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class FinancialReport(Base):

    __tablename__ = "financial_reports"

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

    report_type = Column(Text)
    data = Column(JSONB, default={})
    ai_summary = Column(Text)

    generated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_employees.id"),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
