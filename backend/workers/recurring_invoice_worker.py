"""Scheduled recurring-invoice generation worker.

Each morning (see ``workers.celery_app`` beat schedule) this scans invoices that
have a recurrence configuration (``recurrence_period`` set) and a
``next_billing_date`` that has arrived (``<= today``). For every due invoice it:

1. creates a NEW ``Invoice`` for the next billing cycle, copying the customer,
   the amount, and the line items of the source invoice (status ``unpaid``);
2. advances the source invoice's ``next_billing_date`` by ``recurrence_interval``
   in ``recurrence_period`` units.

Runs are idempotent by construction: once an invoice is generated its
``next_billing_date`` moves into the future, so a second run on the same day
finds nothing due and creates nothing. The generated invoice is a plain,
non-recurring bill — only the source keeps chaining cycles.
"""
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from workers.celery_app import celery_app

logger = logging.getLogger("workers.recurring_invoice")

_PERIODS = {"daily", "weekly", "monthly", "yearly"}


def _advance_date(base, interval: int, period: str):
    """Advance ``base`` by ``interval`` periods (month/year via relativedelta)."""
    from dateutil.relativedelta import relativedelta

    period = (period or "").lower()
    if period == "daily":
        return base + relativedelta(days=interval)
    if period == "weekly":
        return base + relativedelta(weeks=interval)
    if period == "monthly":
        return base + relativedelta(months=interval)
    if period == "yearly":
        return base + relativedelta(years=interval)
    raise ValueError(f"unsupported recurrence period: {period!r}")


@celery_app.task(name="workers.generate_due_recurring_invoices")
def generate_due_recurring_invoices(organization_id=None) -> dict:
    """Generate invoices for every due recurring invoice.

    ``organization_id`` optionally scopes the scan (used by tests / ad-hoc
    runs). Returns ``{"generated": n, "skipped": n}``.
    """
    from app.models.invoice import Invoice, InvoiceItem

    db: Session = SessionLocal()
    try:
        today = date.today()
        query = db.query(Invoice).filter(
            Invoice.recurrence_period.isnot(None),
            Invoice.next_billing_date.isnot(None),
            Invoice.next_billing_date <= today,
        )
        if organization_id is not None:
            query = query.filter(Invoice.organization_id == organization_id)
        due = query.order_by(Invoice.created_at.asc()).all()

        generated = 0
        skipped = 0
        for source in due:
            interval = source.recurrence_interval or 1
            period = (source.recurrence_period or "").lower()
            if period not in _PERIODS or interval <= 0:
                skipped += 1
                continue

            next_date = _advance_date(source.next_billing_date, interval, period)

            new_invoice = Invoice(
                organization_id=source.organization_id,
                customer_id=source.customer_id,
                invoice_number=f"{source.invoice_number or 'INV'}-R",
                amount=source.amount,
                status="unpaid",
                due_date=source.next_billing_date,
            )
            db.add(new_invoice)
            db.flush()

            source_items = (
                db.query(InvoiceItem)
                .filter(InvoiceItem.invoice_id == source.id)
                .all()
            )
            for it in source_items:
                db.add(
                    InvoiceItem(
                        organization_id=source.organization_id,
                        invoice_id=new_invoice.id,
                        product_id=it.product_id,
                        description=it.description,
                        quantity=it.quantity,
                        unit_price=it.unit_price,
                        tax_rate=it.tax_rate,
                        discount=it.discount,
                        line_total=it.line_total,
                        sort_order=it.sort_order,
                    )
                )

            source.next_billing_date = next_date
            db.add(source)
            generated += 1

        db.commit()
        logger.info("recurring invoice scan: generated=%d skipped=%d", generated, skipped)
        return {"generated": generated, "skipped": skipped}
    finally:
        db.close()