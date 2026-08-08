"""ASGI middleware that logs one line per request.

Logs method, path, status code and latency.  It also attaches the caller's
organization id when it is already available in the request context (set by
the auth dependency).  The body, headers and any token material are
intentionally NOT captured.
"""
import time
from uuid import UUID

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import get_logger
from app.middleware.request_context import current_org_id

logger = get_logger("request")


class RequestLoggingMiddleware:
    """Log a structured single-line entry for every HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
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
            elapsed_ms = (time.perf_counter() - start) * 1000
            org = None
            try:
                value = current_org_id.get()
                if isinstance(value, UUID):
                    org = str(value)
            except Exception:
                org = None
            logger.info(
                'method=%s path="%s" status=%s duration_ms=%.1f org_id=%s',
                scope.get("method", ""),
                scope.get("path", ""),
                status_code,
                elapsed_ms,
                org or "-",
            )