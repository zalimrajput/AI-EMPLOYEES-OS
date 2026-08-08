from app.models.ai_conversation import AIConversation
from app.repositories.base import BaseRepository


class AIConversationRepository(BaseRepository):
    model = AIConversation

    def create(self, user_id, ai_employee_id, title: str | None = None):
        return super().create(
            user_id=user_id,
            ai_employee_id=ai_employee_id,
            title=title or "New conversation",
            status="active",
        )