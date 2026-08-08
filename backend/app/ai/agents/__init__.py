"""Agent registry: map an AI employee's role to its agent definition."""
from app.ai.agents.base import AgentDefinition
from app.ai.agents.sales_agent import AGENT as SALES_AGENT
from app.ai.agents.support_agent import AGENT as SUPPORT_AGENT
from app.ai.agents.hr_agent import AGENT as HR_AGENT
from app.ai.agents.recruiter_agent import AGENT as RECRUITER_AGENT
from app.ai.agents.finance_agent import AGENT as FINANCE_AGENT
from app.ai.agents.accountant_agent import AGENT as ACCOUNTANT_AGENT
from app.ai.agents.marketing_agent import AGENT as MARKETING_AGENT
from app.ai.agents.legal_agent import AGENT as LEGAL_AGENT
from app.ai.agents.inventory_agent import AGENT as INVENTORY_AGENT
from app.ai.agents.executive_agent import AGENT as EXECUTIVE_AGENT
from app.ai.agents.content_writer_agent import AGENT as CONTENT_WRITER_AGENT
from app.ai.agents.procurement_agent import AGENT as PROCUREMENT_AGENT

SPECIALIST_AGENTS: list[AgentDefinition] = [
    SALES_AGENT,
    SUPPORT_AGENT,
    HR_AGENT,
    RECRUITER_AGENT,
    FINANCE_AGENT,
    ACCOUNTANT_AGENT,
    MARKETING_AGENT,
    CONTENT_WRITER_AGENT,
    LEGAL_AGENT,
    INVENTORY_AGENT,
    PROCUREMENT_AGENT,
    EXECUTIVE_AGENT,
]

from app.ai.agents.master_agent import make_master, master_system_prompt  # noqa: E402

MASTER_AGENT: AgentDefinition = make_master(
    master_system_prompt([a for a in SPECIALIST_AGENTS if a.key != "master"])
)

ALL_AGENTS: list[AgentDefinition] = [*SPECIALIST_AGENTS, MASTER_AGENT]

DEFAULT_AGENT = AgentDefinition(
    key="general",
    display_name="AI Employee",
    role="General Assistant",
    description="General workspace assistant.",
allowed_tools=[
        "search_crm",
        "get_customer",
        "list_tasks",
        "search_knowledge",
        "get_document",
    ],
    system_prompt=(
        "You are a general-purpose AI employee. Use workspace tools when you "
        "need real data, and answer professionally."
    ),
    role_synonyms=(),
)

_REGISTRY: dict[str, AgentDefinition] = {
    agent.key: agent for agent in ALL_AGENTS
}


def resolve_agent(role: str | None, agent_key: str | None = None) -> AgentDefinition:
    """Pick the best agent for an employee's role (with keyword fallback).

    Exact role matches are preferred over substring synonym matches so
    unambiguous roles (e.g. "Master Coordinator") win even when a synonym of
    another agent happens to be a substring of the role.
    """
    if agent_key and agent_key in _REGISTRY:
        return _REGISTRY[agent_key]
    if role:
        normalized = role.strip().lower()
        for agent in ALL_AGENTS + [DEFAULT_AGENT]:
            if normalized == agent.role.lower():
                return agent
        for agent in ALL_AGENTS + [DEFAULT_AGENT]:
            if agent.matches(role):
                return agent
    return DEFAULT_AGENT


def agent_by_key(key: str) -> AgentDefinition | None:
    return _REGISTRY.get(key)


__all__ = [
    "ALL_AGENTS",
    "DEFAULT_AGENT",
    "MASTER_AGENT",
    "resolve_agent",
    "agent_by_key",
    "AgentDefinition",
]