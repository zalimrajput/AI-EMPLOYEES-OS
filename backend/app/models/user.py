import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):

    __tablename__ = "users"


    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )


    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE"
        ),
        nullable=True
    )


    full_name = Column(
        String,
        nullable=True
    )


    email = Column(
        String,
        nullable=True
    )


    avatar_url = Column(
        String,
        nullable=True
    )


    phone = Column(
        String,
        nullable=True
    )


    status = Column(
        String,
        default="active"
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


    organization = relationship(
        "Organization",
        back_populates="users"
    )

    user_roles = relationship(
        "UserRole",
        backref="user"
    )
