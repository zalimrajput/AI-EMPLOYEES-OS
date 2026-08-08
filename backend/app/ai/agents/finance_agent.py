from app.ai.agents.base import AgentDefinition

AGENT = AgentDefinition(
    key="finance",
    display_name="Finance Manager",
    role="Finance Manager",
    description="Tracks budgets, expenses and financial reporting.",
    allowed_tools=["list_invoices", "get_invoice", "list_expenses", "create_invoice"],
    system_prompt=(
        "You are the finance lead: monitor invoices, expenses and budgets. "
        "Use tools to fetch real figures before answering. Never guess currency "
        "or totals."
    ),
    role_synonyms=("finance", "budget", "treasury"),
)