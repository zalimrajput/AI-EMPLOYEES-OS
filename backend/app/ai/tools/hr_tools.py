"""HR tools: employees, leave requests, candidates."""
from app.ai.tools.base import ToolSpec


def _list_employees(db, org_id, user_id, arguments: dict):
    from app.models.hr import Employee

    rows = (
        db.query(Employee)
        .filter(Employee.organization_id == org_id)
        .limit(arguments.get("limit", 50))
        .all()
    )
    return [
        {
            "id": str(e.id),
            "first_name": e.first_name,
            "last_name": e.last_name,
            "email": e.email,
            "position": e.position,
            "status": e.status,
        }
        for e in rows
    ]


def list_leave_requests(db, org_id, user_id, arguments: dict):
    from app.models.hr import LeaveRequest

    query = db.query(LeaveRequest).filter(LeaveRequest.organization_id == org_id)
    if arguments.get("status"):
        query = query.filter(LeaveRequest.status == arguments["status"])
    rows = query.order_by(LeaveRequest.created_at.desc()).limit(arguments.get("limit", 50)).all()
    return [
        {
            "id": str(l.id),
            "employee_id": str(l.employee_id) if l.employee_id else None,
            "leave_type": l.leave_type,
            "start_date": str(l.start_date) if l.start_date else None,
            "end_date": str(l.end_date) if l.end_date else None,
            "status": l.status,
        }
        for l in rows
    ]


def list_candidates(db, org_id, user_id, arguments: dict):
    from app.models.hr import JobCandidate

    rows = (
        db.query(JobCandidate)
        .filter(JobCandidate.organization_id == org_id)
        .limit(arguments.get("limit", 50))
        .all()
    )
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "email": c.email,
            "status": c.status,
            "ai_score": float(c.ai_score) if c.ai_score is not None else None,
        }
        for c in rows
    ]


HR_TOOLS: dict[str, ToolSpec] = {
    "list_employees": ToolSpec(
        name="list_employees",
        description="List the organization's human employees.",
        parameters={
            "type": "object",
            "properties": {"limit": {"type": "integer"}},
        },
        handler=_list_employees,
    ),
    "list_leave_requests": ToolSpec(
        name="list_leave_requests",
        description="List leave requests, optionally by status.",
        parameters={
            "type": "object",
            "properties": {"status": {"type": "string"}, "limit": {"type": "integer"}},
        },
        handler=list_leave_requests,
    ),
    "list_candidates": ToolSpec(
        name="list_candidates",
        description="List job candidates and their AI scores.",
        parameters={
            "type": "object",
            "properties": {"limit": {"type": "integer"}},
        },
        handler=list_candidates,
    ),
}