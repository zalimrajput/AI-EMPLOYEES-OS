from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.ai_employee import AIEmployee
from app.models.ai_memory import AIMemory


router = APIRouter()


router.include_router(
    crud_router(
        AIEmployee,
        prefix="/ai-employees",
        tags=["AI Employees"],
        search_fields=["name", "role"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        AIMemory,
        prefix="/ai-memories",
        tags=["AI Employees"],
        write_scope="member",
    )
)
