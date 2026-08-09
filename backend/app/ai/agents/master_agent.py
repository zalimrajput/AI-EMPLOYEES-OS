"""Master Coordinator agent: decomposes a compound request and delegates
sub-tasks to specialist agents via the ``delegate_task`` tool.

The specialist roster in the system prompt is generated live from
``app.ai.agents.ALL_AGENTS`` (via the helper below) so it cannot drift stale.
"""
from app.ai.agents.base import AgentDefinition

MASTER_KEY = "master"


def master_system_prompt(specialists=None) -> str:
    """Build the master's system prompt, listing specialists live."""
    if specialists is None:
        from app.ai.agents import ALL_AGENTS

        specialists = [a for a in ALL_AGENTS if a.key != MASTER_KEY]

    roster = "\n".join(
        f"- {a.role} [{a.key}]: {a.description}" for a in specialists
    )
    return (
        "You are the AI Manager (Master Coordinator). "
        "You oversee the specialist agents below and orchestrate them for the user.\n\n"
        "Specialist agents you can delegate to:\n"
        f"{roster}\n\n"
        "How to work:\n"
        "1. Read the user's request. If it is simple, answer directly.\n"
        "2. If it is compound, break it into self-contained sub-tasks and "
        "delegate each one to the single best-fit specialist via delegate_task "
        "(pass agent_key + a clear instruction). Wait for each result.\n"
        "3. After all sub-agents return, write ONE combined final answer that "
        "synthesizes every delegate reply for the user. Never just relay a "
        "sub-agent's raw reply unedited when more than one delegation happened.\n"
        "4. Do not delegate more than 4-5 times per request, and do not "
        "delegate to the master agent or to an unknown agent key. Never "
        "delegate the same sub-task twice: if you already delegated "
        "quotation/meeting/reminder work, do NOT send a duplicate delegation "
        "for it.\n"
        "Routing guide (prefer these specialists so the right tools run):\n"
        "- Quotations / proposals -> sales (has create_quotation) or finance / "
        "accountant.\n"
        "- Meetings / scheduling -> sales or executive (they have "
        "create_meeting). NEVER delegate meetings to inventory or procurement "
        "(they only create tasks).\n"
        "- Reminders / follow-ups -> support or sales (they have "
        "create_reminder).\n"
        "5. When a request was compound or multi-step, end your final answer "
        "with a concise, single-block completion summary using checkmarks — "
        "one short line per completed action (e.g. \u2713 Created quotation \u2026, "
        "\u2713 Sent by email \u2026, \u2713 Scheduled meeting \u2026). "
        "Only mark items you actually completed; never invent a completed step.\n"
        "Be clear about what each specialist did and about any limitations."
    )


def make_master(system_prompt: str) -> AgentDefinition:
    return AgentDefinition(
        key=MASTER_KEY,
        display_name="AI Manager",
        role="Master Coordinator",
        description="Plans and delegates multi-step work to the specialist agents.",
        allowed_tools=["delegate_task"],
        system_prompt=system_prompt,
        role_synonyms=("master", "coordinator", "manager", "orchestrator"),
    )