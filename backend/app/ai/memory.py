"""Semantic worker memory backed by the ``ai_memories`` table.

Memory is scoped per organization and per AI employee. This module stores and
retrieves short context snippets; it does not gate on embeddings yet — if the
vector column is empty we fall back to a lexical ``LIKE`` scan so the engine
keeps working without an embedding provider configured.
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ai_memory import AIMemory

logger = logging.getLogger("app.ai.memory")


def remember(
    db: Session,
    organization_id,
    employee_id,
    content: str,
    metadata: dict | None = None,
) -> AIMemory:
    """Persist a memory snippet for the employee in this org."""
    memory = AIMemory(
        organization_id=organization_id,
        employee_id=employee_id,
        content=content,
        metadata=metadata or {},
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def recall(
    db: Session,
    organization_id,
    employee_id: Optional[str],
    query: str,
    limit: int = 5,
) -> list[str]:
    """Return the most relevant memory contents for this employee."""
    q = db.query(AIMemory).filter(AIMemory.organization_id == organization_id)
    if employee_id is not None:
        q = q.filter(AIMemory.employee_id == employee_id)
    rows = q.order_by(AIMemory.updated_at.desc()).limit(limit).all()
    if not rows:
        return []

    keywords = [w.lower() for w in query.split() if len(w) > 3]
    scored = []
    for row in rows:
        haystack = f"{row.content or ''}".lower()
        if not keywords:
            score = 1
        else:
            score = sum(1 for w in keywords if w in haystack)
        scored.append((score, row))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [row.content for _, row in scored[:limit] if row.content]