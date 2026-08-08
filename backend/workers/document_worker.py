"""Document processing worker: passed filename + bytes out-of-band via a
staging file, runs extraction + indexing.  Kept thin: real logic lives in
``app.services.document_service``.
"""
import logging

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from workers.celery_app import celery_app

logger = logging.getLogger("workers.document")


@celery_app.task(name="workers.process_document", bind=True, max_retries=3)
def process_document_task(
    self,
    organization_id: str,
    uploaded_by: str,
    filename: str,
    stage_path: str,
    title: str | None = None,
):
    from app.services.document_service import ingest_document

    with open(stage_path, "rb") as fh:
        raw = fh.read()

    db: Session = SessionLocal()
    try:
        result = ingest_document(
            db,
            organization_id,
            uploaded_by,
            filename,
            raw,
            title=title,
        )
        return result
    except Exception as exc:
        logger.exception("document processing failed")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()