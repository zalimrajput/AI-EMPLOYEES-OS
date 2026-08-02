import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Organization(Base):

    __tablename__="organizations"


    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )


    name = Column(
        String,
        nullable=False
    )


    slug = Column(
        String,
        nullable=False,
        unique=True
    )


    industry = Column(
        String
    )


    country = Column(
        String
    )


    timezone = Column(
        String,
        default="UTC"
    )


    logo_url = Column(
        String
    )


    settings = Column(
        JSON,
        default={}
    )


    created_by = Column(
        UUID(as_uuid=True),
        nullable=True
    )


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


    users = relationship(
        "User",
        back_populates="organization"
    )


    ai_employees = relationship(
        "AIEmployee",
        back_populates="organization"
    )