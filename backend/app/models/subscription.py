import uuid

from sqlalchemy import (
    Column,
    Text,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
from sqlalchemy.sql import func

from app.models.base import Base


class Plan(Base):

    __tablename__ = "plans"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = Column(
        Text,
        nullable=False,
        unique=True
    )
    description = Column(Text)
    price_monthly = Column(NUMERIC(10, 2), default=0)
    price_yearly = Column(NUMERIC(10, 2), default=0)
    max_users = Column(Integer)
    ai_requests_limit = Column(Integer)
    storage_limit_gb = Column(Integer)
    features = Column(JSONB, default={})
    active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Subscription(Base):

    __tablename__ = "subscriptions"

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

    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plans.id"),
        nullable=False
    )

    status = Column(Text, default="active")
    start_date = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    end_date = Column(DateTime(timezone=True))
    trial_end_date = Column(DateTime(timezone=True))
    payment_provider = Column(Text)
    external_subscription_id = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class BillingTransaction(Base):

    __tablename__ = "billing_transactions"

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

    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True
    )

    amount = Column(NUMERIC(10, 2))
    currency = Column(Text, default="USD")
    payment_status = Column(Text, default="pending")
    payment_provider = Column(Text)
    transaction_reference = Column(Text)
    paid_at = Column(DateTime(timezone=True))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
