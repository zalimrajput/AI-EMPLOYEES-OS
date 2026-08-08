"""Notification worker: best-effort delivery of created notifications.

The DB row is created synchronously by the API; this task is the hook for
future push providers (FCM/APNs) and long-lived Redis fan-out.  No-op-safe.
"""
import logging
from typing import Any

from workers.celery_app import celery_app

logger = logging.getLogger("workers.notification")


@celery_app.task(name="workers.deliver_notification")
def deliver_notification_task(
    notification_id: str,
    organization_id: str,
    user_id: str | None = None,
    payload: dict[str, Any] | None = None,
):
    try:
        from app.realtime.notifications import publish_notification

        publish_notification(
            organization_id=organization_id,
            notification=payload or {},
        )
    except Exception as exc:  # noqa: BLE001 - never fail the queue
        logger.warning("notification delivery failed: %s", exc)
    return {"delivered": True, "id": notification_id}