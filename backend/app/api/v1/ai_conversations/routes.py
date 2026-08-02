from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.ai_conversation import AIConversation


router = APIRouter()


router.include_router(
    crud_router(
        AIConversation,
        prefix="/ai-conversations",
        tags=["AI Conversations"],
        search_fields=["title"],
        write_scope="member",
    )
)
