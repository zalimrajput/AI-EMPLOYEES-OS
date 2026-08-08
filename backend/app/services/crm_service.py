"""CRM business logic beyond the generic CRUD factory."""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.customer import Customer
from app.models.lead import Lead
from app.models.pipeline import Deal


def _count(db: Session, model, organization_id, **filters) -> int:
    query = db.query(model).filter(model.organization_id == organization_id)
    for key, value in filters.items():
        if value is not None:
            query = query.filter(getattr(model, key) == value)
    return query.count()


def get_crm_stats(db: Session, organization_id) -> dict:
    """Aggregate CRM summary counts for dashboard widgets."""
    week_ago = datetime.now() - timedelta(days=7)

    def since(model, **filters) -> int:
        query = db.query(model).filter(
            model.organization_id == organization_id,
            model.created_at >= week_ago,
        )
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(model, key) == value)
        return query.count()

    return {
        "customers_total": _count(db, Customer, organization_id),
        "customers_new_week": since(Customer),
        "leads_total": _count(db, Lead, organization_id),
        "leads_new": _count(db, Lead, organization_id, status="new"),
        "leads_converted": _count(db, Lead, organization_id, status="converted"),
        "deals_total": _count(db, Deal, organization_id),
        "deals_won": _count(db, Deal, organization_id, stage="won"),
        "deals_open": _count(
            db, Deal, organization_id, stage="lead"
        )
        + _count(db, Deal, organization_id, stage="qualified")
        + _count(db, Deal, organization_id, stage="proposal")
        + _count(db, Deal, organization_id, stage="negotiation"),
        "activities_total": _count(db, Activity, organization_id),
        "activities_week": since(Activity),
    }


def _as_uuid(value):
    """Best-effort coercion to a UUID for the numeric entity_id column."""
    from uuid import UUID

    if value is None:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _humanize_type(activity_type: str) -> str:
    """Render a type code as a human-readable action (e.g. "note" -> "Note")."""
    code = (activity_type or "note").replace("_", " ").strip() or "note"
    return code[0].upper() + code[1:]


def log_activity(
    db: Session,
    organization_id,
    user_id,
    target_type: str,
    target_id,
    activity_type: str,
    description: str | None = None,
    metadata: dict | None = None,
) -> Activity:
    # Parameter mapping to the real Activity schema:
    #   target_type   -> entity_type
    #   target_id     -> entity_id  (coerced to UUID)
    #   activity_type -> collapsed with description into the single `action`
    #                    text column, preferring the human-readable description
    #                    and falling back to a humanized type code (matching the
    #                    convention used by workflow_service/on_invoice_paid).
    #   metadata      -> metadata_json
    action = (description or "").strip()
    if not action:
        action = _humanize_type(activity_type)

    row = Activity(
        organization_id=organization_id,
        user_id=user_id,
        entity_type=target_type,
        entity_id=_as_uuid(target_id),
        action=action,
        metadata_json=metadata or {},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row