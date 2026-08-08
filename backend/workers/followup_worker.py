"""Scheduled follow-up reminder worker.

Periodically scans open deals and creates a follow-up Reminder (reusing the
same ``reminders`` table the ``create_reminder`` AI tool writes to) whenever
a customer's most recent contact is older than the stale threshold.

Contact is defined as the most recent of either a CRM Activity on the customer
(``activities.entity_type='customer'`` / ``entity_id=customer.id``) or an
Email belonging to a thread linked to the customer (``email_threads``).
Runs are idempotent: a second run within the dedup window will not duplicate
reminders.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from workers.celery_app import celery_app

logger = logging.getLogger("workers.followup")

STALE_DAYS_DEFAULT = 3
DEDUP_WINDOW_HOURS = 24

# Stages that mean "this deal is done" — no follow-up needed.
_TERMINAL_STAGES = {"won", "lost", "closed_won", "closed_lost", "archived"}


def _last_customer_contact(db: Session, org_id, customer_id) -> datetime | None:
    """Return the most recent contact timestamp for a customer (or None)."""
    from app.models.activity import Activity
    from app.models.email import Email, EmailThread

    last: datetime | None = None

    activity = (
        db.query(Activity)
        .filter(
            Activity.organization_id == org_id,
            Activity.entity_type == "customer",
            Activity.entity_id == customer_id,
        )
        .order_by(Activity.created_at.desc())
        .first()
    )
    if activity is not None and activity.created_at is not None:
        last = activity.created_at

    thread_ids = [
        row[0]
        for row in db.query(EmailThread.id)
        .filter(
            EmailThread.organization_id == org_id,
            EmailThread.customer_id == customer_id,
        )
        .all()
    ]
    if thread_ids:
        email = (
            db.query(Email)
            .filter(Email.thread_id.in_(thread_ids))
            .order_by(Email.sent_at.desc())
            .first()
        )
        stamp = email.sent_at if email is not None else None
        if stamp is not None and (last is None or stamp > last):
            last = stamp

    return last


def _recent_reminder_exists(db: Session, org_id, target_type, target_id, now) -> bool:
    """True if a reminder for the same target was created in the dedup window."""
    from app.models.reminder import Reminder

    cutoff = now - timedelta(hours=DEDUP_WINDOW_HOURS)
    exists = (
        db.query(Reminder.id)
        .filter(
            Reminder.organization_id == org_id,
            Reminder.target_type == target_type,
            Reminder.target_id == target_id,
            Reminder.created_at >= cutoff,
        )
        .first()
    )
    return exists is not None


@celery_app.task(name="workers.check_stale_customer_threads")
def check_stale_customer_threads(
    stale_days: int = STALE_DAYS_DEFAULT, organization_id=None
) -> dict:
    """Create follow-up reminders for customers whose last contact is stale.

    Idempotent: existing reminders within the dedup window prevent duplicates.
    ``organization_id`` optionally scopes the scan (used by tests / ad-hoc runs).
    """
    from app.models.customer import Customer
    from app.models.organization import Organization
    from app.models.pipeline import Deal
    from app.models.reminder import Reminder

    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=stale_days)

        org_query = db.query(Organization.id)
        if organization_id is not None:
            org_query = org_query.filter(Organization.id == organization_id)
        orgs = org_query.all()
        created = 0
        skipped = 0

        for (org_id,) in orgs:
            open_deals = (
                db.query(Deal)
                .filter(
                    Deal.organization_id == org_id,
                    Deal.customer_id.isnot(None),
                )
                .all()
            )
            open_deals = [
                d for d in open_deals if (d.stage or "").lower() not in _TERMINAL_STAGES
            ]

            for deal in open_deals:
                last = _last_customer_contact(db, org_id, deal.customer_id)
                if last is not None and last > cutoff:
                    skipped += 1
                    continue

                if _recent_reminder_exists(
                    db, org_id, "deal", deal.id, now
                ):
                    skipped += 1
                    continue

                customer = db.get(Customer, deal.customer_id)
                customer_name = customer.name if customer is not None else "this customer"
                reminder = Reminder(
                    organization_id=org_id,
                    target_type="deal",
                    target_id=deal.id,
                    remind_at=now,
                    message=(
                        f"No reply from {customer_name} in {stale_days}+ days \u2014 "
                        f"follow up on this deal."
                    ),
                )
                db.add(reminder)
                created += 1

        db.commit()
        logger.info(
            "follow-up scan: created=%d skipped=%d", created, skipped
        )
        return {"created": created, "skipped": skipped}
    finally:
        db.close()