from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.email import Email, EmailThread


router = APIRouter()


router.include_router(
    crud_router(
        EmailThread,
        prefix="/email-threads",
        tags=["Email"],
        search_fields=["subject"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        Email,
        prefix="/emails",
        tags=["Email"],
        search_fields=["sender", "receiver"],
        write_scope="member",
    )
)
