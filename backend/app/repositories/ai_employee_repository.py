from uuid import UUID

from app.models.ai_employee import AIEmployee
from app.repositories.base import BaseRepository


class AIEmployeeRepository(BaseRepository):
    model = AIEmployee

    def get_active(self, employee_id: UUID) -> AIEmployee | None:
        return self.scoped(id=employee_id, active=True).first()

    def list_active(self) -> list[AIEmployee]:
        return self.scoped(active=True).order_by(AIEmployee.name).all()