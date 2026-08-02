from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.ai_message import AIMessage


router = APIRouter()


router.include_router(
    crud_router(
        AIMessage,
        prefix="/ai-messages",
        tags=["AI Messages"],
        write_scope="member",
    )
)
