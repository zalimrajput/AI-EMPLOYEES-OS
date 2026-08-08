"""Base types for declarative AI employees."""
from dataclasses import dataclass, field

from app.ai.prompts import system_prompt


@dataclass(frozen=True)
class AgentDefinition:
    key: str
    display_name: str
    role: str
    description: str
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str = ""
    role_synonyms: tuple[str, ...] = ()

    def build_system_prompt(self, org_name: str | None = None) -> str:
        if self.system_prompt:
            return system_prompt(
                employee_name=self.display_name,
                role=self.role,
                extra_system_prompt=self.system_prompt,
                allowed_tools=self.allowed_tools,
                org_name=org_name,
            )
        return system_prompt(
            employee_name=self.display_name,
            role=self.role,
            extra_system_prompt=(
                f"Your job: act as the {self.role} for the company. Be concise, "
                "accurate and helpful. Use the workspace tools when you need "
                "real data."
            ),
            allowed_tools=self.allowed_tools,
            org_name=org_name,
        )

    def matches(self, role: str) -> bool:
        normalized = role.strip().lower()
        if normalized == self.role.lower():
            return True
        return any(syn.lower() in normalized for syn in self.role_synonyms)