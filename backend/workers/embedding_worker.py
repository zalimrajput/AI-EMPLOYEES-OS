"""Embedding worker: chunks + embeds a stored document's extracted text.

Idempotent: calling it twice replaces the per-chunk articles rather than
duplicating them.  Runs under Celery.
"""
import logging

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.document_service import chunk_text
from workers.celery_app import celery_app

logger = logging.getLogger("workers.embedding")


@celery_app.task(name="workers.embed_document", bind=True, max_retries=3)
def embed_document_task(self, document_id: str, organization_id: str, source: str = "upload"):
    from app.ai.embeddings import embed
    from app.models.document import Document
    from app.models.knowledge_base import KnowledgeArticle

    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.organization_id == organization_id,
        ).first()
        if doc is None or not doc.extracted_text:
            return {"indexed": False, "reason": "no extracted text"}

        chunks = chunk_text(doc.extracted_text)[:50]
        vectors = embed(chunks)
        if vectors is None:
            logger.info("embedding provider unavailable; keeping doc unindexed")
            return {"indexed": False, "reason": "no embeddings provider"}

        doc.embedding = vectors[0]
        # Remove stale chunk articles, then write fresh ones.
        db.query(KnowledgeArticle).filter(
            KnowledgeArticle.organization_id == organization_id,
            KnowledgeArticle.source == source,
        ).filter(KnowledgeArticle.content.in_(chunks)).delete(synchronize_session=False)

        for i, chunk in enumerate(chunks):
            article = KnowledgeArticle(
                organization_id=organization_id,
                title=f"{doc.filename or document_id} — part {i + 1}",
                content=chunk,
                source=source or "document",
            )
            article.embedding = vectors[i]
            db.add(article)

        db.commit()
        return {"indexed": True, "chunks": len(chunks)}
    except Exception as exc:
        logger.exception("embedding failed")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="workers.embed_memory")
def embed_memory_task(memory_id: str, employee_id: str, organization_id: str):
    from app.ai.embeddings import embed
    from app.models.ai_memory import AIMemory

    db: Session = SessionLocal()
    try:
        memory = db.query(AIMemory).filter(AIMemory.id == memory_id).first()
        if memory is None or not memory.content:
            return {"indexed": False}
        vectors = embed([memory.content])
        if vectors:
            memory.embedding = vectors[0]
            db.commit()
        return {"indexed": bool(vectors)}
    except Exception as exc:
        logger.exception("memory embed failed")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()