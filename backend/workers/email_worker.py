"""Transactional email worker.

Sends email best-effort through a single Gmail-sending implementation
(``app.integrations.gmail.service.get_client`` -> ``GmailClient.send_email``),
which handles attachments and 401 token refresh. When the org has no live
Gmail integration the task records the attempt and returns a benign result so
the caller's flow never fails. Runs under Celery.
"""
import logging

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.integrations.gmail.client import IntegrationAuthError, IntegrationNotConnectedError
from workers.celery_app import celery_app

logger = logging.getLogger("workers.email")


@celery_app.task(name="workers.send_email", bind=True, max_retries=3)
def send_email_task(
    self,
    organization_id: str,
    to_email: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
):
    from app.integrations.gmail.service import get_client
    from app.models.email import Email

    db: Session = SessionLocal()
    try:
        try:
            client = get_client(db, organization_id)
        except IntegrationNotConnectedError:
            logger.info("no gmail integration; skipping send for %s", to_email)
            return {"queued": True, "delivered": False, "reason": "no integration"}

        client.send_email(to=to_email, subject=subject, body=body)

        if thread_id:
            email_row = (
                db.query(Email)
                .filter(Email.id == thread_id, Email.organization_id == organization_id)
                .first()
            )
            if email_row is not None:
                email_row.ai_generated = False
                db.commit()
        return {"queued": True, "delivered": True}
    except IntegrationAuthError as exc:
        logger.error("gmail auth failed for %s: %s", to_email, exc)
        return {"queued": True, "delivered": False, "reason": "auth_error"}
    except Exception as exc:
        logger.exception("email task failed; will retry")
        raise self.retry(exc=exc)
    finally:
        db.close()