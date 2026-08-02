from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.task import Task


router = APIRouter()


router.include_router(
    crud_router(
        Task,
        prefix="/tasks",
        tags=["Tasks"],
        search_fields=["title", "description"],
        write_scope="member",
    )
)
