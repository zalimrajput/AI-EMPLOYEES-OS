"""Prompt templates shared by the AI engine."""

TOOL_PROTOCOL = """\
You are an AI Employee inside a business operating system. You execute tools
to fetch or mutate business data before answering when needed.

When you need to call a tool, reply with EXACTLY one line of JSON and nothing
else, matching this shape:

{{to_call: {"name": "TOOL_NAME", "arguments": { ... }}}}

Allowed tools: {tools}
Return plain, professional text to the user once you have the information
you need. Never invent tool results.
"""


def system_prompt(
    employee_name: str,
    role: str,
    extra_system_prompt: str | None,
    allowed_tools: list[str],
    org_name: str | None = None,
) -> str:
    tools_block = ", ".join(sorted(allowed_tools)) if allowed_tools else "none"
    base = (
        f"You are {employee_name}, a specialized AI employee for the role of "
        f"'{role}' in the organization '{(org_name or 'this workspace')}'. "
    )
    if extra_system_prompt:
        base += f"\n{extra_system_prompt}"
    if allowed_tools:
        base += f"\n\nYou have access to the following tools: {tools_block}."
    return base


def with_memory_context(system: str, context_chunks: list[str]) -> str:
    if not context_chunks:
        return system
    joined = "\n\n".join(context_chunks)
    return f"{system}\n\nRelevant context from your workspace:\n{joined}"


def summarize_previous_turn(history: list[dict], max_chars: int = 6000) -> str:
    """Compact the prior assistant/user turn history for re-injection."""
    parts = []
    total = 0
    for turn in reversed(history):
        rendered = f"{turn['role']}: {turn['content']}"
        total += len(rendered)
        if total > max_chars:
            break
        parts.append(rendered)
    return "\n".join(reversed(parts))