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


class Employee(Base):

    __tablename__ = "employees"

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

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    employee_code = Column(Text)
    first_name = Column(
        Text,
        nullable=False
    )
    last_name = Column(Text)
    email = Column(Text)
    phone = Column(Text)

    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=True
    )

    position = Column(Text)
    joining_date = Column(Date)
    salary = Column(NUMERIC)
    status = Column(Text, default="active")
    metadata_json = Column("metadata", JSONB, default={})

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Attendance(Base):

    __tablename__ = "attendance"

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

    employee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=True
    )

    check_in = Column(DateTime(timezone=True))
    check_out = Column(DateTime(timezone=True))
    status = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class LeaveRequest(Base):

    __tablename__ = "leave_requests"

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

    employee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=True
    )

    leave_type = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    reason = Column(Text)
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


class JobCandidate(Base):

    __tablename__ = "job_candidates"

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
    email = Column(Text)
    phone = Column(Text)
    resume_url = Column(Text)
    skills = Column(JSONB, default=[])
    ai_score = Column(NUMERIC)
    status = Column(Text, default="new")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
