"""Guardrail allowlist must always match the tool registry.

Every registered tool must be allowlisted (so executor.run accepts it) and
every allowlisted tool must be registered (no dangling names). This failed
silently twice this session (5 new tools registered but missing from
_SAFE_TOOL_NAMES), so lock it down: if either set drifts, this test fails
loudly in CI instead of at runtime.
"""
import sys

sys.path.insert(0, ".")


def test_tool_registry_matches_guardrails_allowlist():
    from app.ai.guardrails import _SAFE_TOOL_NAMES
    from app.ai.tools import ALL_TOOLS

    registered = set(ALL_TOOLS.keys())
    allowlisted = set(_SAFE_TOOL_NAMES)

    missing_from_allowlist = sorted(registered - allowlisted)
    dangling_in_allowlist = sorted(allowlisted - registered)

    assert not missing_from_allowlist, (
        f"Registered but NOT in _SAFE_TOOL_NAMES (executor.run would reject "
        f"them): {missing_from_allowlist}"
    )
    assert not dangling_in_allowlist, (
        f"In _SAFE_TOOL_NAMES but NOT registered: {dangling_in_allowlist}"
    )
    assert registered == allowlisted


def test_all_agent_allowed_tools_resolve():
    """Every tool an agent lists must exist in the registry."""
    from app.ai.agents import ALL_AGENTS
    from app.ai.tools import ALL_TOOLS

    for agent in ALL_AGENTS:
        missing = [t for t in agent.allowed_tools if t not in ALL_TOOLS]
        assert not missing, (
            f"agent {agent.key!r} references unknown tools: {missing}"
        )
