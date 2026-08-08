"""Executor glue: validation + execution of a single tool call.

Kept separate from the engine so tools can be reused by the streaming endpoint
or webhooks without pulling in the full agent loop.
"""
from typing import Any

from sqlalchemy.orm import Session

from app.ai.guardrails import validate_tool_call
from app.ai.tools import execute_tool


def run(
    db: Session,
    tool_name: str,
    organization_id,
    user_id,
    arguments: dict | None = None,
    allowed_tools: list[str] | None = None,
) -> dict[str, Any]:
    """Validate (guardrails + allowlist) then execute one tool call."""
    arguments = arguments or {}
    if not validate_tool_call(tool_name, arguments):
        return {"error": f"Tool {tool_name!r} is not allowed"}
    if allowed_tools is not None and tool_name not in allowed_tools:
        return {"error": f"Tool {tool_name!r} is not enabled for this agent"}
    return execute_tool(db, tool_name, organization_id, user_id, arguments)