"""Deterministic planning: decompose compound requests into tool-ready steps.

The engine executes a single tool per turn with a step limit. This module
lets a caller know up-front whether a request is a simple answer (no tools)
or needs several sequential tool calls, and returns the ordered plan so the
LLM can be given the plan in its system prompt.
"""
from typing import Any


def is_compound(message: str) -> bool:
    """Heuristic: requests referencing multiple entities or actions."""
    conjunctions = (" and ", ", ", " plus ", "then", "also")
    lower = message.lower()
    return any(word in lower for word in ("list all", "compare", "summarize every") ) or (
        lower.count(" and ") >= 1
        or lower.count(",") >= 2
    )


def suggested_tools(message: str) -> list[str]:
    """Keyword hint for tools likely relevant to the request."""
    lower = message.lower()
    mapping = [
        (("lead", "prospect", "customer"), "search_crm"),
        (("invoice", "bill", "quote"), "list_invoices"),
        (("expense", "spend"), "list_expenses"),
        (("task", "todo", "follow up"), "list_tasks"),
        (("meeting", "interview"), "list_meetings"),
        (("employee", "staff", "hr", "leave"), "list_employees"),
        (("candidate", "hiring", "recruit"), "list_candidates"),
        (("stock", "inventory", "warehouse"), "list_inventory"),
        (("campaign", "marketing"), "list_campaigns"),
    ]
    suggested = []
    for keywords, tool in mapping:
        if any(k in lower for k in keywords):
            suggested.append(tool)
    return suggested[:4]


def plan(message: str) -> dict[str, Any]:
    """Return a small actionable plan for the turn."""
    return {
        "compound": is_compound(message),
        "suggested_tools": is_compound(message) and suggested(message) or [],
    }


def suggested(message: str) -> list[str]:
    return suggested_tools(message)