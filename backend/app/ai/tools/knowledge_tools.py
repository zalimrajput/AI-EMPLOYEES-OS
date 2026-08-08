"""Knowledge base and document tools (RAG retrieval)."""
import json
from uuid import UUID

from app.ai import model_router
from app.ai.tools.base import ToolSpec

_TEXT_LIMIT = 8000
# Hardcoded in Python so a bad LLM completion can never drop it.
DISCLAIMER = "Informational analysis only \u2014 not legal advice. Review with qualified counsel."


def _limit(arguments, default):
    return arguments.get("limit") or default


def _match(query, text):
    return not query or (query in (text or "").lower())


def search_knowledge(db, org_id, user_id, arguments: dict):
    from app.models.knowledge_base import KnowledgeArticle

    query = (arguments.get("query") or "").lower()
    rows = (
        db.query(KnowledgeArticle)
        .filter(KnowledgeArticle.organization_id == org_id)
        .limit(_limit(arguments, 200))
        .all()
    )
    matched = [a for a in rows if _match(query, a.title) or _match(query, a.content)]
    return [
        {
            "id": str(a.id),
            "title": a.title,
            "content": (a.content or "")[:2000],
            "source": a.source,
        }
        for a in matched[: _limit(arguments, 5)]
    ]


def get_document(db, org_id, user_id, arguments: dict):
    from app.models.document import Document

    try:
        doc_id = UUID(arguments["id"])
    except (ValueError, TypeError, KeyError):
        return {"error": "invalid document id"}
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.organization_id == org_id)
        .first()
    )
    if doc is None:
        return {"error": "Document not found"}
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "file_url": doc.file_url,
        "mime_type": doc.mime_type,
        "extracted_text": (doc.extracted_text or "")[:2000],
    }


def _doc_type(parsed: dict) -> str:
    value = (parsed.get("document_type") or "").strip()
    normalized = value.lower()
    allowed = {"nda", "msa", "lease", "unknown"}
    if normalized in allowed:
        return normalized
    # fuzzy: return the raw value if short, else unknown
    return value[:30] or "unknown"


def _document_prompt(text: str, focus: str | None) -> list[dict]:
    instruction = (
        "This is informational analysis only \u2014 NOT legal advice. Provide a "
        "general, non-committal overview and defer every judgment to a "
        "qualified attorney."
    )
    if focus:
        instruction += f" Pay particular attention to: {focus}"
    return [
        {
            "role": "system",
            "content": (
                instruction + " Respond with ONLY a JSON object using exactly "
                "these keys: summary (str), document_type (str: NDA, MSA, "
                "lease, or unknown), key_terms (list of {\"term\": str, "
                "\"detail\": str}), risks (list of str), "
                "missing_or_unusual (list of str)."
            ),
        },
        {"role": "user", "content": text},
    ]


def _parse_doc_json(raw) -> dict | None:
    if not raw or not isinstance(raw, str):
        return None
    text = raw.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _empty_terms(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    terms = []
    for entry in value[:20]:
        if not isinstance(entry, dict):
            continue
        term = (entry.get("term") or "").strip()
        if not term:
            continue
        terms.append(
            {"term": str(term)[:200], "detail": str(entry.get("detail") or "")[:400]}
        )
    return terms


def _strs(value) -> list[str]:
    return [str(s)[:300] for s in value if isinstance(s, str)][:20] if isinstance(value, list) else []


def _text(value) -> str:
    return str(value).strip() if value else ""


def _analyze_document(db, org_id, user_id, arguments: dict):
    from app.models.document import Document

    try:
        doc_id = UUID(arguments["document_id"])
    except (ValueError, TypeError, KeyError):
        return {"error": "invalid document id"}
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.organization_id == org_id)
        .first()
    )
    if doc is None:
        return {"error": "Document not found"}

    raw_text = doc.extracted_text or ""
    if not raw_text.strip():
        return {"error": "Document has no extracted text to analyze"}

    truncated = False
    message_text = raw_text
    if len(raw_text) > _TEXT_LIMIT:
        truncated = True
        message_text = raw_text[:_TEXT_LIMIT]

    focus = _text(arguments.get("focus"))

    fallback = {
        "summary": "Automated analysis unavailable.",
        "document_type": "unknown",
        "key_terms": [],
        "risks": [],
        "missing_or_unusual": [],
        "source": "data",
        "disclaimer": DISCLAIMER,
        "truncated": truncated,
    }

    try:
        raw = model_router.complete(_document_prompt(message_text, focus), temperature=0.2)
        parsed = _parse_doc_json(raw)
    except Exception:  # noqa: BLE001 - rate limit / no key / parse issues -> fallback
        parsed = None

    if parsed is None or not _text(parsed.get("summary")):
        return fallback

    return {
        "summary": _text(parsed.get("summary"))[:1200],
        "document_type": _doc_type(parsed),
        "key_terms": _empty_terms(parsed.get("key_terms")),
        "risks": _strs(parsed.get("risks")),
        "missing_or_unusual": _strs(parsed.get("missing_or_unusual")),
        "source": "llm",
        "disclaimer": DISCLAIMER,
        "truncated": truncated,
    }


KNOWLEDGE_TOOLS: dict[str, ToolSpec] = {
    "search_knowledge": ToolSpec(
        name="search_knowledge",
        description="Search the internal knowledge base by title or content.",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
        },
        handler=search_knowledge,
    ),
    "get_document": ToolSpec(
        name="get_document",
        description="Fetch a document's metadata and extracted text by id.",
        parameters={
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
        handler=get_document,
    ),
    "analyze_document": ToolSpec(
        name="analyze_document",
        description=(
            "Analyze a document's extracted text (contracts, NDAs, MSAs, "
            "leases, etc.) for key terms, risks and oddities. Informational "
            "only, not legal advice."
        ),
        parameters={
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "format": "uuid"},
                "focus": {
                    "type": "string",
                    "description": "Optional focus, e.g. 'termination clauses'.",
                },
            },
            "required": ["document_id"],
        },
        handler=_analyze_document,
    ),
}