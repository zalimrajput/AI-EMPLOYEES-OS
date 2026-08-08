from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.v1._crud import crud_router
from app.core.config import settings
from app.core.database import get_db
from app.integrations.whatsapp.client import WhatsAppError, WhatsAppNotConnectedError
from app.integrations.whatsapp.service import (
    get_client,
    get_or_create_contact,
    resolve_organization_id,
)
from app.models.whatsapp import WhatsAppContact, WhatsAppMessage


router = APIRouter()


router.include_router(
    crud_router(
        WhatsAppContact,
        prefix="/whatsapp-contacts",
        tags=["WhatsApp"],
        search_fields=["name", "phone"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        WhatsAppMessage,
        prefix="/whatsapp-messages",
        tags=["WhatsApp"],
        write_scope="member",
    )
)


@router.get("/whatsapp/webhook", tags=["WhatsApp"])
# Public endpoint: Meta verification handshake when the webhook is subscribed.
def verify_webhook(
    mode: str | None = Query(default=None, alias="hub.mode"),
    verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    if mode == "subscribe" and verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(challenge or "")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp/webhook", tags=["WhatsApp"])
# Public endpoint: Meta delivers inbound WhatsApp messages here.
def receive_webhook(
    payload: dict,
    db: Session = Depends(get_db),
):
    entries = payload.get("entry") or []
    processed = 0
    errors: list[str] = []
    for entry in entries:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for message in value.get("messages") or []:
                try:
                    if _handle_inbound(db, value, message):
                        processed += 1
                except WhatsAppNotConnectedError:
                    errors.append("whatsapp not connected")
                except Exception as exc:  # noqa: BLE001
                    errors.append(str(exc))
    return {"received": "true", "processed": processed, "errors": errors}


def _handle_inbound(db, value: dict, message: dict) -> bool:
    """Process one inbound message; returns True when we handled it.

    Returns False (silently) when the message belongs to an undocumented
    phone number so unknown senders never error the webhook loop.
    """
    from app.ai.orchestrator import execute_turn
    from app.ai.guardrails import is_flagged, refuse_reply
    from app.models.ai_conversation import AIConversation
    from app.models.ai_message import AIMessage

    from_number = str(message.get("from") or "").strip()
    if not from_number:
        return False

    phone_number_id = str((value.get("metadata") or {}).get("phone_number_id") or "")
    organization_id = None
    if phone_number_id:
        organization_id = resolve_organization_id(db, phone_number_id)

    # No integration row for this phone number -> drop silently (not ours).
    if organization_id is None:
        return False

    name = None
    contacts = value.get("contacts") or []
    for c in contacts:
        if str(c.get("wa_id") or "") == from_number:
            name = (c.get("profile") or {}).get("name")
            break

    contact = get_or_create_contact(db, organization_id, from_number, name)

    body = _extract_text(message)

    inbound = WhatsAppMessage(
        organization_id=organization_id,
        contact_id=contact.id,
        direction="inbound",
        ai_generated=False,
        message=body,
        media=_extract_media(message),
    )
    db.add(inbound)

    conversation = _get_or_create_conversation(db, organization_id, contact.id)
    user_msg = AIMessage(
        organization_id=organization_id,
        conversation_id=conversation.id,
        role="user",
        message=body,
    )
    user_msg.message_metadata = {"source": "whatsapp"}
    db.add(user_msg)
    db.commit()

    if is_flagged(body):
        reply_text = refuse_reply()
    else:
        history = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation.id)
            .order_by(AIMessage.created_at)
            .limit(20)
            .all()
        )
        reply_text, _agent_key = execute_turn(
            db,
            organization_id,
            str(conversation.user_id) if conversation.user_id else None,
            conversation,
            body,
            history_messages=history,
        )

    reply_msg = AIMessage(
        organization_id=organization_id,
        conversation_id=conversation.id,
        role="assistant",
        message=reply_text,
    )
    reply_msg.message_metadata = {"source": "whatsapp"}
    outbound = WhatsAppMessage(
        organization_id=organization_id,
        contact_id=contact.id,
        direction="outgoing",
        ai_generated=True,
        message=reply_text,
        media={},
    )
    db.add(reply_msg)
    db.add(outbound)
    db.commit()

    _send_reply(db, organization_id, phone_number_id, from_number, reply_text)
    return True


def _get_or_create_conversation(db, organization_id, contact_id):
    from app.models.ai_conversation import AIConversation

    conversation = (
        db.query(AIConversation)
        .filter(
            AIConversation.organization_id == organization_id,
            AIConversation.title == f"whatsapp:{contact_id}",
        )
        .first()
    )
    if conversation is None:
        conversation = AIConversation(
            organization_id=organization_id,
            user_id=_get_or_create_bot_user(db, organization_id).id,
            title=f"whatsapp:{contact_id}",
            status="active",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return conversation


def _get_or_create_bot_user(db, organization_id):
    """Return the org's dedicated WhatsApp bot user (created lazily).

    Inbound WhatsApp events carry no authenticated platform user, but the
    ``ai_conversations.user_id`` column is NOT NULL, so each tenant gets one
    scoped bot user that owns WhatsApp-threaded AI conversations.
    """
    from app.models.user import User

    user = (
        db.query(User)
        .filter(
            User.organization_id == organization_id,
            User.email == "whatsapp-bot@local",
        )
        .first()
    )
    if user is None:
        user = User(
            organization_id=organization_id,
            full_name="WhatsApp Bot",
            email="whatsapp-bot@local",
            status="active",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _extract_text(message: dict) -> str:
    text = (message.get("text") or {}).get("body") or ""
    return str(text).strip()


def _extract_media(message: dict) -> dict | None:
    mtype = message.get("type")
    if mtype in ("audio", "image", "video", "document", "sticker"):
        media = message.get(mtype) or {}
        return {
            "type": mtype,
            "media_id": media.get("id"),
            "mime_type": media.get("mime_type"),
            "filename": media.get("filename"),
        }
    return None


def _send_reply(db, organization_id, phone_number_id, to_number, reply_text) -> None:
    try:
        client = get_client(db, organization_id, phone_number_id=phone_number_id)
        client.send_text(to_number, reply_text)
    except (WhatsAppNotConnectedError, WhatsAppError):
        return None