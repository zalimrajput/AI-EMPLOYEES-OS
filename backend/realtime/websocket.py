"""WebSocket connection manager with per-org room fan-out.

Usage (FastAPI):
    from app.realtime.websocket import manager

    manager.connect_org(org_id, websocket)   # on accept
    await manager.send_org(org_id, {...})    # delivers to all sockets in room
    manager.disconnect(websocket)            # on client disconnect
"""
import asyncio
import json
import logging
from typing import Any, NoReturn

from fastapi import WebSocket

logger = logging.getLogger("realtime.websocket")


class ConnectionManager:
    def __init__(self) -> None:
        self._org_connections: dict[str, set[WebSocket]] = {}
        self._conn_org: dict[int, str] = {}

    async def connect(self, websocket: WebSocket, org_id: str) -> None:
        await websocket.accept()
        ws_id = id(websocket)
        self._conn_org[ws_id] = org_id
        self._org_connections.setdefault(org_id, set()).add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        ws_id = id(websocket)
        org_id = self._conn_org.pop(ws_id, None)
        if org_id:
            room = self._org_connections.get(org_id)
            if room and websocket in room:
                room.discard(websocket)
                if not room:
                    self._org_connections.pop(org_id, None)

    async def send_org(self, org_id: str, payload: Any) -> None:
        text = json.dumps(payload, default=str)
        for ws in list(self._org_connections.get(org_id, ())):
            try:
                await ws.send_text(text)
            except Exception:
                self.disconnect(ws)

    async def broadcast(self, payload: Any) -> None:
        for org_id in list(self._org_connections.keys()):
            await self.send_org(org_id, payload)


manager = ConnectionManager()


async def handle_ws_stream(websocket: WebSocket, org_id: str) -> NoReturn:
    """Dedicated socket for AI token streaming / keepalive heartbeat."""
    await manager.connect(websocket, org_id)
    try:
        await websocket.send_json({"type": "connected"})
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        manager.disconnect(websocket)