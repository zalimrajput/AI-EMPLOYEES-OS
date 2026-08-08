"""Realtime notification fan-out (wraps the event bus)."""
from typing import Any

from realtime.events import publish


def publish_notification(
    organization_id: str,
    notification: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> None:
    """Publish a notification event to subscribed dashboard sockets."""
    publish(
        f"org:{organization_id}:notifications",
        {"notification": notification, "metadata": metadata or {}},
    )