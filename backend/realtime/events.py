"""In-process event bus used by the realtime layer.

Redis PubSub is used when REDIS_URL is reachable; otherwise a thread-safe
in-process hub keeps the system fully functional in a single-node demo.
"""
import asyncio
import json
import logging
import threading
from collections import defaultdict
from typing import Any, Awaitable, Callable

logger = logging.getLogger("realtime.events")

_subscribers: dict[str, list[Callable[[str, dict], Awaitable[None] | None]]] = defaultdict(list)
_lock = threading.Lock()


def subscribe(channel: str, handler) -> None:
    with _lock:
        _subscribers[channel].append(handler)


def unsubscribe(channel: str, handler) -> None:
    with _lock:
        if handler in _subscribers.get(channel, []):
            _subscribers[channel].remove(handler)


def publish(channel: str, payload: dict | None = None) -> None:
    """Dispatch to local subscribers (sync fire-and-forget) + Redis when up."""
    payload = payload or {}

    for handler in list(_subscribers.get(channel, [])):
        try:
            result = handler(channel, payload)
            if asyncio.iscoroutine(result):
                _schedule(result)
        except Exception:
            logger.exception("event handler failed", exc_info=True)

    try:
        import redis

        from app.core.config import settings

        client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        client.publish(channel, json.dumps(payload, default=str))
    except Exception:
        pass  # Redis optional


def _schedule(coro) -> None:
    async def run():
        await coro

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_run_awaited(coro))
        else:
            loop.run_until_complete(_run_awaited(coro))
    except Exception:
        logger.exception("failed to deliver async event", exc_info=True)


async def _run_awaited(coro):
    return await coro