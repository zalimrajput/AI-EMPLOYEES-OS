"""Text embedding helpers for pgvector storage.

Uses the OpenAI embeddings API when ``OPENAI_API_KEY`` is set; otherwise the
retriever falls back to keyword matching so RAG still works in a demo setup.
"""
import logging
from typing import Optional

logger = logging.getLogger("app.ai.embeddings")


def embed(texts: list[str]) -> Optional[list[list[float]]]:
    """Return a list of vectors for the given texts, or None if unsupported."""
    from app.core.config import settings

    if not settings.OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.embeddings.create(
            model=settings.EMBEDDING_MODEL, input=texts
        )
        return [item.embedding for item in resp.data]
    except Exception as exc:  # noqa: BLE001
        logger.warning("embedding failure: %s", exc, exc_info=True)
        return None


def embed_text(text: str) -> Optional[list[float]]:
    result = embed([text])
    return result[0] if result else None