"""Notifications + realtime socket API.

- ``GET/MARK notifications`` stay REST for reads/marking read.
- ``/ws`` accepts a Supabase JWT via ``?token=`` and streams per-org events
  (notifications, AI token chunks) over the WebSocket.
"""
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.v1._crud import require_org_member
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.notification import Notification
from app.models.user import User
from realtime.websocket import manager
from app.services.notification_service import (
    create_notification,
    list_notifications,
    mark_read,
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("/")
def get_notifications(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    return list_notifications(db, me.organization_id, user_id=None, limit=limit)


@router.post("")
def create_note(
    title: str,
    message: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    return create_notification(
        db,
        me.organization_id,
        me.id,
        title,
        message,
        notification_type="info",
    )


@router.post("/{notification_id}/read")
def read_notification(
    notification_id,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    note = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.organization_id == me.organization_id,
        )
        .first()
    )
    if note is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Notification not found")
    return mark_read(db, note, True)


@router.websocket("/ws")
async def notifications_socket(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    from app.core.auth import verify_supabase_token

    try:
        payload = verify_supabase_token(token)
        me: User = require_org_member(db, payload)
        org_id = str(me.organization_id)
    except Exception:
        await websocket.close(code=4401)
        return

    await manager.connect(websocket, org_id)

    # attach handler stream: send any events publish()ed for this org
    from realtime.events import subscribe

    async def forward(channel: str, data: dict):
        if channel == f"org:{org_id}:notifications":
            await websocket.send_json(data)

    subscribe(f"org:{org_id}:notifications", forward)
    try:
        await websocket.send_json({"type": "connected", "org": org_id})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        from realtime.events import unsubscribe

        unsubscribe(f"org:{org_id}:notifications", forward)
        manager.disconnect(websocket)