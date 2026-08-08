"""Audit logging. Writes one row per auditable action to ``audit_logs``.

Configured with the same session used by the request, so writes are atomic
with the action that produced them.  Never include tokens, secrets or request
bodies in the metadata.
"""
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_log import AuditLog


def record_audit(
    db: Session,
    organization_id,
    user_id,
    action: str,
    entity: str,
    metadata: dict[str, Any] | None = None,
) -> AuditLog | None:
    """Create an audit log row unless auditing has been disabled in config."""
    if not settings.AUDIT_LOG_ENABLED:
        return None
    row = AuditLog(
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        entity=entity,
        metadata=metadata or {},
    )
    db.add(row)
    return row


def commit_audit(db: Session, row: AuditLog) -> None:
    db.commit()
    db.refresh(row)