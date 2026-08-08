from app.ai.agents.base import AgentDefinition

AGENT = AgentDefinition(
    key="inventory",
    display_name="Inventory Manager",
    role="Operations Manager",
    description="Tracks stock, suppliers and purchase orders.",
    allowed_tools=["search_crm", "list_inventory", "list_suppliers", "create_task"],
    system_prompt=(
        "You watch inventory levels, suppliers and purchase orders. Recommend "
        "reorders from real stock data."
    ),
    role_synonyms=("inventory", "stock", "warehouse", "operations"),
)