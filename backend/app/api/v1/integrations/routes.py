from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.integration import Integration


router = APIRouter()


router.include_router(
    crud_router(
        Integration,
        prefix="/integrations",
        tags=["Integrations"],
        search_fields=["provider"],
    )
)
