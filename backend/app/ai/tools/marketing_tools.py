"""Marketing tools: campaigns and content."""
from app.ai.tools.base import ToolSpec


def list_campaigns(db, org_id, user_id, arguments: dict):
    from app.models.marketing import MarketingCampaign

    query = db.query(MarketingCampaign).filter(MarketingCampaign.organization_id == org_id)
    if arguments.get("status"):
        query = query.filter(MarketingCampaign.status == arguments["status"])
    rows = query.order_by(MarketingCampaign.created_at.desc()).limit(arguments.get("limit", 50)).all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "campaign_type": c.campaign_type,
            "status": c.status,
            "budget": float(c.budget) if c.budget is not None else None,
        }
        for c in rows
    ]


def create_email_draft(db, org_id, user_id, arguments: dict):
    from app.models.email import Email, EmailThread
    from uuid import UUID

    subject = arguments.get("subject") or ""
    body = arguments.get("body") or ""
    thread_id = None
    try:
        tid = arguments.get("thread_id")
        if tid:
            thread_id = UUID(tid)
    except (ValueError, TypeError):
        thread_id = None

    if thread_id is None:
        thread = EmailThread(
            organization_id=org_id,
            subject=subject[:200] or "AI draft",
            participants={},
            summary=None,
        )
        db.add(thread)
        db.flush()
        thread_id = thread.id

    email = Email(
        organization_id=org_id,
        thread_id=thread_id,
        sender=str(user_id) if user_id else None,
        receiver=arguments.get("receiver"),
        body=body,
        direction="outbound",
        ai_generated=True,
    )
    db.add(email)
    db.commit()
    return {"id": str(email.id), "thread_id": str(thread_id), "subject": subject, "draft": True}


_BODY_LIMIT = 1000
_EMAILS_CAP = 10


def _uuid(value):
    from uuid import UUID

    try:
        return UUID(str(value)) if value else None
    except (ValueError, TypeError):
        return None


def _classify_prompt(subject: str, messages: list[str], removed_chars: int) -> list[dict]:
    context = {
        "subject": subject,
        "recent_messages": messages,
        "truncated_chars": removed_chars,
    }
    return [
        {
            "role": "system",
            "content": (
                "You classify an email thread. Respond with ONLY a JSON object "
                "using exactly these keys: priority (\"low\"|\"normal\"|"
                "\"high\"|\"urgent\"), category (a short label like \"sales "
                "inquiry\", \"support issue\", \"billing question\", \"spam\" "
                "or \"other\"), requires_response (boolean), reasoning "
                "(1 sentence). Judge by tone and deadlines in the messages."
            ),
        },
        {
            "role": "user",
            "content": "Thread: {subject}\n\nMessages:\n".format(subject=subject)
            + "\n---\n".join(messages),
        },
    ]


def _classify_email_thread(db, org_id, user_id, arguments: dict):
    """On-demand email thread classification (called explicitly, not on arrival)."""
    from app.ai import model_router
    from app.models.email import Email, EmailThread

    thread_id = _uuid(arguments.get("thread_id"))
    thread = (
        db.query(EmailThread)
        .filter(EmailThread.id == thread_id, EmailThread.organization_id == org_id)
        .first()
    )
    if thread is None:
        return {"error": "Email thread not found"}

    emails = (
        db.query(Email)
        .filter(Email.thread_id == thread.id)
        .order_by(Email.created_at.desc())
        .limit(_EMAILS_CAP)
        .all()
    )

    removed_chars = 0
    raw_bodies = []
    for email in emails:
        body = email.body or ""
        if len(body) > _BODY_LIMIT:
            removed_chars += len(body) - _BODY_LIMIT
            body = body[: _BODY_LIMIT]
        raw_bodies.append(body)

    fallback = {
        "priority": "normal",
        "category": "unclassified",
        "requires_response": True,
        "reasoning": "Automated classification unavailable.",
        "source": "data",
    }

    result = None
    try:
        messages = _classify_prompt(thread.subject or "", raw_bodies, removed_chars)
        raw = model_router.complete(messages, temperature=0.2)
        parsed = _parse_classification_json(raw)
        if parsed is not None:
            result = {
                "priority": parsed.get("priority", "normal"),
                "category": parsed.get("category", "unclassified"),
                "requires_response": bool(parsed.get("requires_response", False)),
                "reasoning": parsed.get("reasoning", ""),
                "source": "llm",
            }
    except Exception:  # noqa: BLE001 - never break the agent loop on a model error
        result = None

    if result is None:
        result = fallback

    if result["priority"] in ("low", "normal", "high", "urgent"):
        thread.ai_priority = result["priority"]
    category = result.get("category")
    if category:
        thread.category = category
    db.add(thread)
    db.commit()
    db.refresh(thread)

    return {
        "thread_id": str(thread.id),
        "priority": thread.ai_priority,
        "category": thread.category,
        "requires_response": result["requires_response"],
        "reasoning": str(result.get("reasoning") or ""),
        "source": result["source"],
    }


def _parse_classification_json(raw) -> dict | None:
    import json

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


def _summarize_prompt(subject: str, messages: list[str], removed_chars: int) -> list[dict]:
    context = {
        "subject": subject,
        "recent_messages": messages,
        "truncated_chars": removed_chars,
    }
    return [
        {
            "role": "system",
            "content": (
                "You summarize a business email thread. Respond with ONLY a "
                "JSON object using exactly one key: summary (a concise 2-4 "
                "sentence summary of the whole conversation, including any "
                "open asks or next steps). Do not invent details not in the "
                "messages."
            ),
        },
        {
            "role": "user",
            "content": "Thread: {subject}\n\nMessages:\n".format(subject=subject)
            + "\n---\n".join(messages),
        },
    ]


def _first_sentences(text: str | None, n: int = 2) -> str:
    import re

    text = (text or "").strip()
    if not text:
        return "No readable message content yet."
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(s for s in sentences[:n] if s).strip()


def _summarize_email_thread(db, org_id, user_id, arguments: dict):
    """Summarize an email thread and persist EmailThread.summary."""
    from app.ai import model_router
    from app.models.email import Email, EmailThread

    thread_id = _uuid(arguments.get("thread_id"))
    thread = (
        db.query(EmailThread)
        .filter(EmailThread.id == thread_id, EmailThread.organization_id == org_id)
        .first()
    )
    if thread is None:
        return {"error": "Email thread not found"}

    emails = (
        db.query(Email)
        .filter(Email.thread_id == thread.id)
        .order_by(Email.created_at.desc())
        .limit(_EMAILS_CAP)
        .all()
    )

    removed_chars = 0
    raw_bodies = []
    for email in emails:
        body = email.body or ""
        if len(body) > _BODY_LIMIT:
            removed_chars += len(body) - _BODY_LIMIT
            body = body[: _BODY_LIMIT]
        raw_bodies.append(body)

    # Data-only fallback: first ~2 sentences of the latest email body.
    fallback_summary = _first_sentences(emails[0].body if emails else None)

    source = "data"
    try:
        messages = _summarize_prompt(thread.subject or "", raw_bodies, removed_chars)
        raw = model_router.complete(messages, temperature=0.2)
        parsed = _parse_classification_json(raw)
        if isinstance(parsed, dict) and parsed.get("summary"):
            fallback_summary = str(parsed["summary"])
            source = "llm"
    except Exception:  # noqa: BLE001 - never break the agent loop on a model error
        source = "data"

    thread.summary = fallback_summary.strip()
    db.add(thread)
    db.commit()
    db.refresh(thread)

    return {
        "thread_id": str(thread.id),
        "summary": thread.summary,
        "source": source,
    }


MARKETING_TOOLS: dict[str, ToolSpec] = {
    "list_campaigns": ToolSpec(
        name="list_campaigns",
        description="List marketing campaigns, optionally by status.",
        parameters={
            "type": "object",
            "properties": {"status": {"type": "string"}, "limit": {"type": "integer"}},
        },
        handler=list_campaigns,
    ),
    "create_email_draft": ToolSpec(
        name="create_email_draft",
        description="Create an AI draft email (or within an existing thread).",
        parameters={
            "type": "object",
            "properties": {
                "receiver": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "thread_id": {"type": "string"},
            },
        },
        handler=create_email_draft,
    ),
    "classify_email_thread": ToolSpec(
        name="classify_email_thread",
        description=(
            "Classify an email thread's urgency (low/normal/high/urgent) and "
            "category (e.g. sales inquiry, support issue, billing question, "
            "spam) from its subject and recent messages, persisting the result."
        ),
        parameters={
            "type": "object",
            "properties": {"thread_id": {"type": "string", "format": "uuid"}},
            "required": ["thread_id"],
        },
        handler=_classify_email_thread,
    ),
    "summarize_email_thread": ToolSpec(
        name="summarize_email_thread",
        description=(
            "Write and persist a concise 2-4 sentence summary of an email "
            "thread's conversation onto EmailThread.summary."
        ),
        parameters={
            "type": "object",
            "properties": {"thread_id": {"type": "string", "format": "uuid"}},
            "required": ["thread_id"],
        },
        handler=_summarize_email_thread,
    ),
}