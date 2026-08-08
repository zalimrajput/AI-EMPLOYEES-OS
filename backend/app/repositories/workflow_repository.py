from app.models.workflow import Workflow
from app.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository):
    model = Workflow

    def list_active(self) -> list[Workflow]:
        return self.scoped(active=True).order_by(Workflow.created_at.desc()).all()