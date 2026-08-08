"""WhatsApp worker: sends messages via the configured WhatsApp provider.

Best-effort: if no token/phone id are configured the task is a no-op so the
queue never fails on missing demo credentials.
"""
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from workers.celery_app import celery_app

logger = logging.getLogger("workers.whatsapp")


@celery_app.task(name="workers.send_whatsapp", bind=True, max_retries=2)
def send_whatsapp_task(
    self,
    organization_id: str,
    to_number: str,
    message: str,
):
    token = getattr(settings, "WHATSAPP_API_TOKEN", None)
    phone_id = getattr(settings, "WHATSAPP_PHONE_ID", None)
    if not (token and phone_id):
        return {"sent": False, "reason": "whatsapp not configured"}

    import httpx

    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    resp = httpx.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message},
        },
        timeout=30,
    )
    if resp.status_code >= 300:
        logger.warning("whatsapp send failed: %s %s", resp.status_code, resp.text[:200])
        raise RuntimeError("whatsapp send failed")
    return {"sent": True, "message_id": (resp.json() or {}).get("messages", [{}])[0].get("id")}