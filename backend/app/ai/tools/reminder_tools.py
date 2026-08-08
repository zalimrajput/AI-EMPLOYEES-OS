"""Reminder tools."""
from uuid import UUID

from app.ai.tools.base import ToolSpec


def _optional_uuid(value):
    try:
        return UUID(str(value)) if value else None
    except (ValueError, TypeError):
        return None


def _parse_dt(value):
    from datetime import datetime

    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def create_reminder(db, org_id, user_id, arguments: dict):
    """Create a future reminder row for a target record."""
    from app.models.reminder import Reminder

    remind_at = _parse_dt(arguments.get("remind_at"))
    if remind_at is None:
        return {"error": "remind_at must be a valid ISO datetime"}

    reminder = Reminder(
        organization_id=org_id,
        user_id=_optional_uuid(user_id),
        target_type=arguments.get("target_type"),
        target_id=_optional_uuid(arguments.get("target_id")),
        remind_at=remind_at,
        message=arguments.get("message"),
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return {
        "id": str(reminder.id),
        "target_type": reminder.target_type,
        "target_id": str(reminder.target_id) if reminder.target_id else None,
        "remind_at": reminder.remind_at.isoformat() if reminder.remind_at else None,
        "message": reminder.message,
        "triggered": bool(reminder.triggered),
    }


def list_reminders(db, org_id, user_id, arguments: dict):
    """List upcoming (not yet triggered) reminders, optionally by target_type."""
    from app.models.reminder import Reminder

    query = (
        db.query(Reminder)
        .filter(Reminder.organization_id == org_id, Reminder.triggered.is_(False))
    )
    if arguments.get("target_type"):
        query = query.filter(Reminder.target_type == arguments["target_type"])
    rows = (
        query.order_by(Reminder.remind_at.asc())
        .limit(arguments.get("limit", 50))
        .all()
    )
    return [
        {
            "id": str(r.id),
            "target_type": r.target_type,
            "target_id": str(r.target_id) if r.target_id else None,
            "remind_at": r.remind_at.isoformat() if r.remind_at else None,
            "message": r.message,
            "triggered": bool(r.triggered),
        }
        for r in rows
    ]


REMINDER_TOOLS: dict[str, ToolSpec] = {
    "create_reminder": ToolSpec(
        name="create_reminder",
        description="Create a reminder to follow up on a target record later.",
        parameters={
            "type": "object",
            "properties": {
                "target_type": {"type": "string"},
                "target_id": {"type": "string"},
                "remind_at": {"type": "string", "description": "ISO datetime"},
                "message": {"type": "string"},
            },
            "required": ["target_type", "remind_at"],
        },
        handler=create_reminder,
    ),
    "list_reminders": ToolSpec(
        name="list_reminders",
        description="List upcoming reminders, optionally filtered by target_type.",
        parameters={
            "type": "object",
            "properties": {
                "target_type": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
        handler=list_reminders,
    ),
}