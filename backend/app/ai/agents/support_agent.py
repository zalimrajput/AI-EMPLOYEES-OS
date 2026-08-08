from app.ai.agents.base import AgentDefinition

AGENT = AgentDefinition(
    key="support",
    display_name="Customer Support",
    role="Customer Support",
    description="Answers customer questions and drafts replies.",
    allowed_tools=["search_crm", "get_customer", "summarize_customer", "list_tasks", "create_activity", "classify_email_thread", "summarize_email_thread"],
    system_prompt=(
        "You support customers politely and efficiently. Use the CRM to pull "
        "account context and create notebook-worthy support activities. "
        "Escalate anything legally or financially risky to a human."
    ),
    role_synonyms=("support", "help desk", "customer success", "service"),
)