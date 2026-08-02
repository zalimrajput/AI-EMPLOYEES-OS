from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.api_key import APIKey, APIRequest


router = APIRouter()


router.include_router(
    crud_router(
        APIKey,
        prefix="/api-keys",
        tags=["API Keys"],
        search_fields=["name"],
    )
)


router.include_router(
    crud_router(
        APIRequest,
        prefix="/api-requests",
        tags=["API Keys"],
        write_scope="member",
    )
)
