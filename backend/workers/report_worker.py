"""Report worker: renders a resource-heavy report / PDF generation.

The heavy lifting lives in ``app.services.invoice_service`` and
``app.services.billing_service``; this worker is the async hook so report
generation doesn't block the request thread.
"""
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from workers.celery_app import celery_app

logger = logging.getLogger("workers.report")


@celery_app.task(name="workers.generate_report", bind=True, max_retries=3)
def generate_report_task(
    self,
    organization_id: str,
    user_id: str | None,
    report_type: str,
    params: dict[str, Any] | None = None,
):
    params = params or {}
    db: Session = SessionLocal()
    try:
        from app.services.crm_service import get_crm_stats

        snapshot = get_crm_stats(db, organization_id)

        report = report_row(db, organization_id, user_id, report_type, snapshot)
        db.add(report)
        db.commit()
        db.refresh(report)
        return {"report_id": str(report.id), "ok": True}
    except Exception as exc:
        logger.exception("report generation failed")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


def report_row(db, organization_id, user_id, report_type, snapshot):
    from app.models.report import Report

    return Report(
        organization_id=organization_id,
        name=f"{report_type or 'Report'} generated",
        report_type=report_type,
        parameters={"generated_by_user": user_id},
        result=snapshot,
        ai_summary=None,
    )