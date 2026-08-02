from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.api_key import Webhook


router = APIRouter()


router.include_router(
    crud_router(
        Webhook,
        prefix="/webhooks",
        tags=["Webhooks"],
        search_fields=["name", "url"],
    )
)
