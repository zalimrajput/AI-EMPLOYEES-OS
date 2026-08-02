from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.workflow import Workflow


router = APIRouter()


router.include_router(
    crud_router(
        Workflow,
        prefix="/workflows",
        tags=["Workflows"],
        search_fields=["name", "trigger"],
        write_scope="member",
    )
)
