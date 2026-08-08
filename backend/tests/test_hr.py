"""Real-DB smoke tests for HR tools (list_employees, list_leave_requests, list_candidates)."""
import sys
import uuid
from datetime import date

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text


def _teardown(db, org):
    for statement in [
        "DELETE FROM attendance WHERE organization_id = :id",
        "DELETE FROM leave_requests WHERE organization_id = :id",
        "DELETE FROM job_candidates WHERE organization_id = :id",
        "DELETE FROM employees WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _org(db):
    from app.models.organization import Organization

    org = Organization(name="HR Org", slug=f"hr-{uuid.uuid4().hex[:10]}", settings={})
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.mark.db
def test_list_employees_handler_returns_real_row(db):
    from app.ai.tools.hr_tools import HR_TOOLS
    from app.models.hr import Employee

    org = _org(db)
    emp = Employee(
        organization_id=org.id,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        position="Engineer",
        status="active",
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)

    try:
        result = HR_TOOLS["list_employees"].handler(db, org.id, None, {})
        assert any(e["id"] == str(emp.id) for e in result)
        row = next(e for e in result if e["id"] == str(emp.id))
        assert row["first_name"] == "Jane"
        assert row["last_name"] == "Doe"
        assert row["position"] == "Engineer"
        assert row["status"] == "active"
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_list_leave_requests_handler_filters_by_status(db):
    from app.ai.tools.hr_tools import HR_TOOLS
    from app.models.hr import LeaveRequest

    org = _org(db)
    lr = LeaveRequest(
        organization_id=org.id,
        leave_type="vacation",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 5),
        status="approved",
    )
    db.add(lr)
    db.commit()
    db.refresh(lr)

    try:
        approved = HR_TOOLS["list_leave_requests"].handler(
            db, org.id, None, {"status": "approved"}
        )
        assert any(x["id"] == str(lr.id) for x in approved)
        row = next(x for x in approved if x["id"] == str(lr.id))
        assert row["leave_type"] == "vacation"
        assert row["status"] == "approved"

        pending = HR_TOOLS["list_leave_requests"].handler(
            db, org.id, None, {"status": "pending"}
        )
        assert all(x["id"] != str(lr.id) for x in pending)
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_list_candidates_handler_returns_real_row(db):
    from app.ai.tools.hr_tools import HR_TOOLS
    from app.models.hr import JobCandidate

    org = _org(db)
    cand = JobCandidate(
        organization_id=org.id,
        name="Sam Lee",
        email="sam@example.com",
        status="shortlisted",
        ai_score=87,
    )
    db.add(cand)
    db.commit()
    db.refresh(cand)

    try:
        result = HR_TOOLS["list_candidates"].handler(db, org.id, None, {})
        assert any(c["id"] == str(cand.id) for c in result)
        row = next(c for c in result if c["id"] == str(cand.id))
        assert row["name"] == "Sam Lee"
        assert row["status"] == "shortlisted"
        assert row["ai_score"] == 87.0
    finally:
        _teardown(db, org)