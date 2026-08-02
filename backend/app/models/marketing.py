import uuid

from sqlalchemy import (
    Column,
    Text,
    Integer,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
from sqlalchemy.sql import func

from app.models.base import Base


class MarketingCampaign(Base):

    __tablename__ = "marketing_campaigns"

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
    campaign_type = Column(Text)
    status = Column(Text, default="draft")
    start_date = Column(Date)
    end_date = Column(Date)
    budget = Column(NUMERIC(12, 2))

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class AudienceSegment(Base):

    __tablename__ = "audience_segments"

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
    rules = Column(JSONB, default={})
    customer_count = Column(Integer, default=0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class MarketingContent(Base):

    __tablename__ = "marketing_content"

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

    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("marketing_campaigns.id", ondelete="CASCADE"),
        nullable=True
    )

    content_type = Column(Text)
    title = Column(Text)
    content = Column(Text)
    ai_generated = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)
    metadata_json = Column("metadata", JSONB, default={})

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class EmailCampaign(Base):

    __tablename__ = "email_campaigns"

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

    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("marketing_campaigns.id", ondelete="CASCADE"),
        nullable=True
    )

    subject = Column(Text)
    template = Column(Text)
    sent_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
