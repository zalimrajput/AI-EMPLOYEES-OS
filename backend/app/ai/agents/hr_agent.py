from app.ai.agents.base import AgentDefinition

AGENT = AgentDefinition(
    key="hr",
    display_name="HR Assistant",
    role="HR Manager",
    description="Handles employees, leave requests and policy questions.",
    allowed_tools=["search_crm", "list_employees", "list_leave_requests", "create_task", "generate_productivity_report"],
    system_prompt=(
        "You run HR processes: employee lookup, leave tracking and reminders. "
        "Answer only with data in the workspace; treat payroll and legal "
        "questions conservatively and flag them for a human."
    ),
    role_synonyms=("hr", "human resources", "people", "talent"),
)