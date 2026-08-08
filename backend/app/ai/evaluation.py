"""Evaluation / answer-quality checkpoints (no LLM required).

Kept deterministic so tests can assert behaviour without a network call.
"""
from typing import Any

_ANSWER_REQUIRED_MIN = 5


def reply_too_short(reply: str) -> bool:
    return len((reply or "").strip()) < _ANSWER_REQUIRED_MIN


def has_refusal_marker(reply: str) -> bool:
    lowered = (reply or "").lower()
    return ("i can't" in lowered or "i cannot" in lowered or "refuse" in lowered)


def evaluate(reply: str) -> dict[str, Any]:
    return {
        "too_short": reply_too_short(reply),
        "refusal": has_refusal_marker(reply),
        "length": len(reply or ""),
    }