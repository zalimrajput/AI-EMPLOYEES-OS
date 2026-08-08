"""Retrieval of context chunks for the AI engine (documents + knowledge base).

Uses pgvector cosine search when an embedding model/keys are configured,
otherwise falls back to a keyword scan so RAG still works in a demo setup.
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.knowledge_base import KnowledgeArticle

logger = logging.getLogger("app.ai.retriever")


def _vector_ok() -> bool:
    try:
        from app.core.config import settings

        return bool(settings.OPENAI_API_KEY)
    except Exception:
        return False


def _embed_query(query: str):
    from app.ai.embeddings import embed

    vectors = embed([query])
    return vectors[0] if vectors else None


def _vector_search_articles(
    db: Session, organization_id, vector, limit: int
) -> list[KnowledgeArticle]:
    from sqlalchemy import text

    sql = text(
        "SELECT id, title, content, source "
        "FROM knowledge_articles WHERE organization_id = :org "
        "AND embedding IS NOT NULL "
        "ORDER BY embedding <=> :v ASC LIMIT :lim"
    )
    rows = db.execute(sql, {"org": str(organization_id), "v": vector, "lim": limit})
    return [
        KnowledgeArticle(
            id=r[0], title=r[1], content=r[2], source=r[3]
        )
        for r in rows
    ]


def retrieve_documents(
    db: Session, organization_id, query: str, limit: int = 4
) -> list[dict]:
    """Return document text chunks relevant to the query."""
    vector = _embed_query(query)
    if vector is not None:
        from sqlalchemy import text

        sql = text(
            "SELECT filename, extracted_text "
            "FROM documents WHERE organization_id = :org "
            "AND embedding IS NOT NULL "
            "ORDER BY embedding <=> :v LIMIT :limit"
        )
        rows = db.execute(
            sql, {"org": str(organization_id), "v": vector, "limit": limit}
        ).fetchall()
        return [
            {"title": r[0] or "Document", "content": (r[1] or "")[:2000], "source": "document"}
            for r in rows
        ]
    # keyword fallback
    rows = (
        db.query(Document)
        .filter(Document.organization_id == organization_id)
        .order_by(Document.created_at.desc())
        .limit(50)
        .all()
    )
    query_lower = query.lower()
    keywords = [w for w in query_lower.split() if len(w) > 3]
    scored = []
    for doc in rows:
        text = (doc.extracted_text or "")[:4000]
        if not text:
            continue
        score = text.lower().count(query_lower)
        score += sum(text.lower().count(w) for w in keywords)
        if score:
            scored.append((score, doc))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {
            "title": doc.filename,
            "content": (doc.extracted_text or "")[:2000],
            "source": "document",
        }
        for _, doc in scored[:limit]
    ]


def retrieve_articles(
    db: Session, organization_id, query: str, limit: int = 4
) -> list[dict]:
    vector = _embed_query(query)
    if vector is not None:
        rows = _vector_search_articles(db, organization_id, vector, limit)
        return [
            {
                "title": a.title,
                "content": (a.content or "")[:2000],
                "source": a.source or "knowledge_base",
            }
            for a in rows
        ]
    rows = (
        db.query(KnowledgeArticle)
        .filter(KnowledgeArticle.organization_id == organization_id)
        .order_by(KnowledgeArticle.updated_at.desc())
        .limit(50)
        .all()
    )
    query_lower = query.lower()
    keywords = [w for w in query_lower.split() if len(w) > 3]
    scored = []
    for article in rows:
        haystack = f"{article.title or ''} {article.content or ''}".lower()
        score = haystack.count(query_lower)
        score += sum(haystack.count(w) for w in keywords)
        if score:
            scored.append((score, article))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {
            "title": article.title,
            "content": (article.content or "")[:2000],
            "source": "knowledge_base",
        }
        for _, article in scored[:limit]
    ]


def retrieve_context(
    db: Session,
    organization_id,
    query: str,
    limit: int = 4,
    include_documents: bool = True,
    include_articles: bool = True,
) -> list[dict]:
    """Combined RAG context as plain dicts for ``with_memory_context``."""
    results: list[dict] = []
    if include_documents:
        results.extend(retrieve_documents(db, organization_id, query, limit))
    if include_articles:
        results.extend(retrieve_articles(db, organization_id, query, limit))
    return results[:limit]