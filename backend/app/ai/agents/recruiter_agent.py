from app.ai.agents.base import AgentDefinition

AGENT = AgentDefinition(
    key="recruiter",
    display_name="Recruiter",
    role="Recruiter",
    description="Screens candidates, schedules interviews and manages pipelines.",
    allowed_tools=["search_crm", "list_candidates", "create_task", "create_meeting", "summarize_meeting", "transcribe_meeting_audio"],
    system_prompt=(
        "You manage recruitment: candidate evaluation, interview scheduling "
        "and follow-ups. Rely on candidate records and meeting tools."
    ),
    role_synonyms=("recruit", "hiring", "talent acquisition", "talent acquisition"),
)