"""ASGI audit-log middleware.

Writes a structured, append-only style log line for every state-changing
request (POST/PUT/PATCH/DELETE) with the caller's user and organization from
the request context.  The body and headers are never logged; only method,
path and status.  Audit records are emitted to the "audit" logger — the
logging configuration routes them to a dedicated sink in production.
"""
import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import get_logger
from app.middleware.request_context import current_org_id, current_user

logger = get_logger("audit")

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AuditMiddleware:
    """Emit one audit record per mutating request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    @staticmethod
    def _identity() -> tuple[str, str]:
        user = current_user.get()
        user_id = user.get("sub", "-") if isinstance(user, dict) else "-"
        org = current_org_id.get()
        return user_id, (str(org) if org else "-")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") not in _MUTATING_METHODS:
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 0

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            status_code = status_code or 500
            raise
        finally:
            user_id, org_id = self._identity()
            logger.info(
                'audit event=request method=%s path="%s" status=%s '
                "user_id=%s org_id=%s duration_ms=%.1f",
                scope.get("method", ""),
                scope.get("path", ""),
                status_code,
                user_id,
                org_id,
                (time.perf_counter() - start) * 1000,
            )
