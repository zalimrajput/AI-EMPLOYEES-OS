"""Notification creation and delivery.

Creates a row in ``notifications`` and, when the Redis broker is reachable,
best-effort publishes an event that the realtime layer fans out to connected
dashboard WebSockets.  If Redis is down the notification still persists.
"""
from typing import Any

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    organization_id,
    user_id,
    title: str,
    message: str,
    notification_type: str = "info",
    metadata: dict[str, Any] | None = None,
) -> Notification:
    row = Notification(
        organization_id=organization_id,
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        read=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    try:
        from realtime.notifications import publish_notification

        publish_notification(
            organization_id=str(row.organization_id),
            notification={
                "id": str(row.id),
                "title": row.title,
                "message": row.message,
                "type": row.type,
                "read": row.read,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            },
            metadata=metadata or {},
        )
    except Exception:
        pass  # realtime is best-effort; the DB row is the source of truth
    return row


def list_notifications(
    db: Session, organization_id, user_id=None, limit: int = 50
) -> list[Notification]:
    query = db.query(Notification).filter(
        Notification.organization_id == organization_id
    )
    if user_id is not None:
        query = query.filter(Notification.user_id == user_id)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


def mark_read(db: Session, notification, read: bool = True) -> Notification:
    notification.read = read
    db.commit()
    db.refresh(notification)
    return notification