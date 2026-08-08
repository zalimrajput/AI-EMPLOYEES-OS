"""ASGI rate-limit middleware (in-process sliding window).

Each client (IP by default, user id when the request context already resolved
one) may make at most ``max_requests`` calls per ``window_seconds``.  Exceeding
the limit returns 429 without touching the application.  The counters live in
memory, which is appropriate for single-process deployments; multi-worker
setups should rely on the API gateway or a Redis-backed limiter instead.
"""
import time
from collections import defaultdict, deque

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.logging import get_logger
from app.middleware.request_context import current_org_id, current_user

logger = get_logger("rate_limit")

DEFAULT_MAX_REQUESTS = 600
DEFAULT_WINDOW_SECONDS = 60


class RateLimitExceeded(Exception):
    """Raised internally when the client exceeded its quota."""


class RateLimitMiddleware:
    """Per-client sliding-window limiter returning 429 responses."""

    def __init__(
        self,
        app: ASGIApp,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
    ) -> None:
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: defaultdict[str, deque] = defaultdict(deque)
        self._lock = __import__("threading").Lock()

    def _client_key(self, scope: Scope) -> str:
        user = current_user.get()
        if user and isinstance(user, dict) and user.get("sub"):
            return f"user:{user['sub']}"
        org = current_org_id.get()
        if org:
            return f"org:{org}"
        client = scope.get("client")
        return f"ip:{client[0] if client else 'unknown'}"

    def _allow(self, key: str, now: float) -> bool:
        with self._lock:
            window = self._hits[key]
            cutoff = now - self.window_seconds
            while window and window[0] <= cutoff:
                window.popleft()
            if len(window) >= self.max_requests:
                return False
            window.append(now)
            return True

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if not self._allow(self._client_key(scope), time.time()):
            logger.warning("rate limit exceeded client=%s", self._client_key(scope))
            body = b'{"detail": "Rate limit exceeded. Try again later."}'
            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return

        await self.app(scope, receive, send)
