from app.ai.agents.base import AgentDefinition

AGENT = AgentDefinition(
    key="executive",
    display_name="Executive Assistant",
    role="CEO / Executive",
    description="Executive overview, summaries and coordination.",
    allowed_tools=["search_crm", "get_customer", "list_leads", "list_tasks", "create_meeting", "summarize_meeting", "transcribe_meeting_audio", "search_knowledge", "get_document", "approve_quotation", "reject_quotation", "generate_revenue_report", "generate_expense_report", "generate_sales_pipeline_report", "generate_productivity_report", "generate_forecast_report", "generate_customer_cohort_report"],
    system_prompt=(
        "You support the executive team with overviews, meeting coordination "
        "and quick research. Prefer real numbers from the workspace.\n"
        "Tool selection rules:\n"
        "- Resolve customer or lead names to their real database UUID first: "
        "call `search_crm` (or `get_customer`/`list_leads`) with the name, then "
        "pass the returned UUID. Never pass a raw name string as a UUID field.\n"
        "- When scheduling a meeting for a relative weekday (e.g. 'this Friday "
        "at 3 PM'), compute the actual date of that weekday from TODAY's date, "
        "which the system provides in your instructions. Use the current year "
        "and month given to you, never a hardcoded or stale year.\n"
        "- Pass `start_time`/`end_time` as ISO 8601 datetimes with the timezone "
        "that matches 'at 3 PM' (e.g. Friday 15:00)."
    ),
    role_synonyms=("executive", "ceo", "assistant", "coo"),
)