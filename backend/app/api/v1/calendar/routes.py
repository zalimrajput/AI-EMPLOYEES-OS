from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.meeting import Meeting


router = APIRouter()


router.include_router(
    crud_router(
        Meeting,
        prefix="/meetings",
        tags=["Calendar"],
        search_fields=["title"],
        write_scope="member",
    )
)
