"""Tool specification type and handler protocol.

Every tool handler receives the caller's ``organization_id`` and ``user_id``
so tenant scoping is guaranteed in code (defense in depth on top of RLS).
Handlers intentionally call the **service layer** — never duplicate SQL — and
return JSON-serializable values only.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

ToolHandler = Callable[[Session, Optional[Any], Optional[Any], dict], Any]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler

    def to_definition(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }