"""Email tools: send email (optionally with attachments) via Gmail."""
from app.ai.tools.base import ToolSpec


def _uuid(value):
    from uuid import UUID

    try:
        return UUID(str(value)) if value else None
    except (ValueError, TypeError):
        return None


def send_email(db, org_id, user_id, arguments: dict):
    """Send a real email (optionally with attachments) via Gmail."""
    from app.integrations.gmail.client import (
        IntegrationAuthError,
        IntegrationNotConnectedError,
    )
    from app.integrations.gmail.service import get_client

    to = arguments.get("to")
    if not to:
        return {"error": "to is required"}
    subject = arguments.get("subject") or ""
    body = arguments.get("body") or ""

    try:
        result = get_client(db, org_id).send_email(
            to=to,
            subject=subject,
            body=body,
            cc=arguments.get("cc"),
            bcc=arguments.get("bcc"),
            attachments=arguments.get("attachments"),
        )
    except IntegrationNotConnectedError:
        return {
            "error": "Gmail isn't connected for this organization — "
            "connect it in Settings first."
        }
    except IntegrationAuthError as exc:
        return {"error": f"Gmail authentication failed: {exc}"}
    return result


def send_quotation_email(db, org_id, user_id, arguments: dict):
    """Generate a quotation PDF and email it to the recipient."""
    from app.models.quotation import Quotation
    from app.services.invoice_service import generate_quotation_pdf

    quotation = (
        db.query(Quotation)
        .filter(
            Quotation.id == _uuid(arguments.get("quotation_id")),
            Quotation.organization_id == org_id,
        )
        .first()
    )
    if quotation is None:
        return {"error": "Quotation not found"}

    if quotation.status != "approved":
        return {
            "error": (
                "Quotation must be approved before sending — currently in "
                f"status: {quotation.status}"
            )
        }

    try:
        buffer = generate_quotation_pdf(db, org_id, quotation)
    except Exception as exc:  # noqa: BLE001 - report to the caller
        return {"error": f"{exc.__class__.__name__}: {exc}"}

    number = quotation.quotation_number or str(quotation.id)
    result = send_email(
        db,
        org_id,
        user_id,
        {
            "to": arguments.get("to"),
            "subject": arguments.get("subject") or f"Quotation {number}",
            "body": arguments.get("body") or "",
            "cc": arguments.get("cc"),
            "bcc": arguments.get("bcc"),
            "attachments": [
                {
                    "filename": f"Quotation-{number}.pdf",
                    "content_bytes": buffer.getvalue(),
                    "mime_type": "application/pdf",
                }
            ],
        },
    )
    if "error" not in result:
        quotation.status = "sent"
        db.add(quotation)
        db.commit()
        db.refresh(quotation)
    return result


_ATTACHMENT_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "content_bytes": {"type": "string"},
            "mime_type": {"type": "string"},
        },
    },
}

_EMAIL_PROPS = {
    "to": {"type": "string", "description": "Recipient email address."},
    "subject": {"type": "string"},
    "body": {"type": "string"},
    "cc": {"type": "string", "description": "Optional CC address(es)."},
    "bcc": {"type": "string", "description": "Optional BCC address(es)."},
}


EMAIL_TOOLS: dict[str, ToolSpec] = {
    "send_email": ToolSpec(
        name="send_email",
        description=(
            "Send a real email from the organization's connected Gmail "
            "account. Fails with a clear error when Gmail isn't connected."
        ),
        parameters={
            "type": "object",
            "properties": {**_EMAIL_PROPS, "attachments": _ATTACHMENT_SCHEMA},
            "required": ["to", "subject", "body"],
        },
        handler=send_email,
    ),
    "send_quotation_email": ToolSpec(
        name="send_quotation_email",
        description=(
            "Generate a PDF for an existing quotation and send it as an email "
            "attachment from the organization's connected Gmail account."
        ),
        parameters={
            "type": "object",
            "properties": {
                **_EMAIL_PROPS,
                "quotation_id": {"type": "string"},
            },
            "required": ["quotation_id", "to"],
        },
        handler=send_quotation_email,
    ),
}
