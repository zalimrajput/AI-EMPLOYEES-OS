"""Billing: plans catalog + the org's active subscription / usage posture."""
from sqlalchemy.orm import Session

from app.models.api_key import APIKey
from app.models.storage import StorageQuota
from app.models.subscription import Plan, Subscription
from app.models.usage import UsageRecord


def list_plans(db: Session) -> list[Plan]:
    return db.query(Plan).order_by(Plan.price_monthly).all()


def get_or_default_plan(db: Session) -> Plan | None:
    return db.query(Plan).filter(Plan.active.is_(True)).order_by(Plan.price_monthly).first()


def get_subscription(db: Session, organization_id) -> dict | None:
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.organization_id == organization_id,
            Subscription.status == "active",
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if sub is None:
        return None
    plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
    return {
        "id": str(sub.id),
        "plan_id": str(sub.plan_id),
        "plan_name": plan.name if plan else None,
        "status": sub.status,
        "start_date": sub.start_date,
        "end_date": sub.end_date,
        "trial_end_date": sub.trial_end_date,
        "payment_provider": sub.payment_provider,
        "external_subscription_id": sub.external_subscription_id,
    }


def get_usage_summary(db: Session, organization_id) -> dict:
    ai_requests = (
        db.query(UsageRecord)
        .filter(
            UsageRecord.organization_id == organization_id,
            UsageRecord.usage_type == "ai_request",
        )
        .count()
    )
    quota = (
        db.query(StorageQuota)
        .filter(StorageQuota.organization_id == organization_id)
        .first()
    )
    api_keys = (
        db.query(APIKey)
        .filter(
            APIKey.organization_id == organization_id,
            APIKey.active.is_(True),
        )
        .count()
    )
    return {
        "ai_requests": ai_requests,
        "storage_used_bytes": quota.used_storage_bytes if quota else 0,
        "storage_max_bytes": quota.max_storage_bytes if quota else 1073741824,
        "active_api_keys": api_keys,
    }


def get_billing_overview(db: Session, organization_id) -> dict:
    """Everything the billing page needs in one response."""
    return {
        "subscription": get_subscription(db, organization_id),
        "usage": get_usage_summary(db, organization_id),
        "plans": [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "price_monthly": p.price_monthly,
                "price_yearly": p.price_yearly,
                "max_users": p.max_users,
                "ai_requests_limit": p.ai_requests_limit,
                "storage_limit_gb": p.storage_limit_gb,
                "active": p.active,
            }
            for p in list_plans(db)
        ],
    }