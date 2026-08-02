from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.marketing import (
    AudienceSegment,
    EmailCampaign,
    MarketingCampaign,
    MarketingContent,
)


router = APIRouter()


router.include_router(
    crud_router(
        MarketingCampaign,
        prefix="/campaigns",
        tags=["Marketing"],
        search_fields=["name"],
    )
)


router.include_router(
    crud_router(
        AudienceSegment,
        prefix="/audience-segments",
        tags=["Marketing"],
        search_fields=["name"],
    )
)


router.include_router(
    crud_router(
        MarketingContent,
        prefix="/marketing-content",
        tags=["Marketing"],
        search_fields=["title"],
    )
)


router.include_router(
    crud_router(
        EmailCampaign,
        prefix="/email-campaigns",
        tags=["Marketing"],
        search_fields=["subject"],
    )
)
