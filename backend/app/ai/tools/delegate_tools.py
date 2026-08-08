"""Delegation tool for the Master agent.

Exposes a single ``delegate_task`` tool so the orchestration agent can hand a
sub-task off to a specialist agent. Engine imports stay lazy (inside the
handler) so importing this module never triggers a circular import.
"""
from app.ai.tools.base import ToolSpec

MASTER_KEY = "master"


def delegate_task(db, org_id, user_id, arguments: dict):
    """Run a sub-task against a specialist agent, in the same org/user.

    Hard guard: never allow delegating to the master itself, and never allow
    an unknown agent key. Failures are returned as a structured error dict.
    """
    agent_key = arguments.get("agent_key")
    instruction = arguments.get("instruction")
    if not agent_key or not instruction:
        return {"error": "agent_key and instruction are required"}

    if agent_key == MASTER_KEY:
        return {"error": f"Unknown or disallowed agent_key: {agent_key}"}

    from app.ai.agents import agent_by_key

    agent = agent_by_key(agent_key)
    if agent is None:
        return {"error": f"Unknown or disallowed agent_key: {agent_key}"}

    try:
        from app.ai.engine import run_agent

        reply = run_agent(
            db,
            organization_id=org_id,
            user_id=user_id,
            agent=agent,
            user_message=instruction,
        )
    except Exception as exc:  # noqa: BLE001 - never raise into the master loop
        return {"error": f"delegation to {agent_key} failed: {exc.__class__.__name__}: {exc}"}

    return {"agent": agent.key, "reply": reply}


DELEGATE_TOOLS: dict[str, ToolSpec] = {
    "delegate_task": ToolSpec(
        name="delegate_task",
        description=(
            "Delegate a single sub-task to a specialist agent by agent_key. "
            "Use only for self-contained, single-agent tasks you cannot do "
            "yourself; do not delegate to the master agent or to an unknown "
            "agent key."
        ),
        parameters={
            "type": "object",
            "properties": {
                "agent_key": {"type": "string", "description": "Specialist agent key to delegate to."},
                "instruction": {"type": "string", "description": "The sub-task to give that agent."},
            },
            "required": ["agent_key", "instruction"],
        },
        handler=delegate_task,
    ),
}