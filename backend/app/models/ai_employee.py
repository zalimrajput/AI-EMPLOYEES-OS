import uuid

from sqlalchemy import (
    Column,
    Text,
    Boolean,
    ForeignKey
)

from sqlalchemy.dialects.postgresql import UUID, JSONB

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func

from app.models.base import Base



class AIEmployee(Base):

    __tablename__="ai_employees"


    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )


    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id"
        ),
        nullable=False
    )


    name = Column(
        Text,
        nullable=False
    )


    role = Column(
        Text,
        nullable=False
    )


    description = Column(Text)


    model = Column(
        Text,
        default="gpt-5"
    )


    system_prompt = Column(Text)


    tools = Column(
        JSONB,
        default={}
    )


    permissions = Column(
        JSONB,
        default={}
    )


    active = Column(
        Boolean,
        default=True
    )


    organization = relationship(
        "Organization",
        back_populates="ai_employees"
    )