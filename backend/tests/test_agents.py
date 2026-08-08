"""Agent definition tests."""
import sys

sys.path.insert(0, ".")

from app.ai.agents import (
    ALL_AGENTS,
    DEFAULT_AGENT,
    agent_by_key,
    resolve_agent,
)


def test_all_agents_unique_keys():
    keys = [a.key for a in ALL_AGENTS]
    assert len(keys) == len(set(keys))
    assert DEFAULT_AGENT.key not in keys


def test_agents_have_tools_and_prompt():
    for agent in ALL_AGENTS:
        assert agent.display_name
        assert agent.role
        assert agent.description
        assert agent.system_prompt
        assert isinstance(agent.allowed_tools, list)
        assert agent.allowed_tools, agent.key


def test_allowed_tools_exist_in_registry():
    from app.ai.tools import get_tool

    for agent in ALL_AGENTS + [DEFAULT_AGENT]:
        for tool in agent.allowed_tools:
            assert get_tool(tool) is not None, f"{agent.key}:{tool}"


def test_agent_by_key_and_fallback():
    assert agent_by_key("sales").key == "sales"
    assert agent_by_key("does-not-exist") is None
    assert resolve_agent(None).key == "general"
    assert resolve_agent("Sales Manager", agent_key="support").key == "support"


def test_system_prompt_buildable():
    prompt = DEFAULT_AGENT.build_system_prompt(org_name="Acme")
    assert "Acme" in prompt


def test_content_writer_and_procurement_resolve_to_dedicated_agents():
    content = resolve_agent("content writer")
    assert content.key == "content_writer"
    assert content is not agent_by_key("marketing")

    procurement = resolve_agent("procurement")
    assert procurement.key == "procurement"
    assert procurement is not agent_by_key("inventory")

    assert agent_by_key("content_writer").key == "content_writer"
    assert agent_by_key("procurement").key == "procurement"