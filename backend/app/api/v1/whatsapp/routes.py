from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.whatsapp import WhatsAppContact, WhatsAppMessage


router = APIRouter()


router.include_router(
    crud_router(
        WhatsAppContact,
        prefix="/whatsapp-contacts",
        tags=["WhatsApp"],
        search_fields=["name", "phone"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        WhatsAppMessage,
        prefix="/whatsapp-messages",
        tags=["WhatsApp"],
        write_scope="member",
    )
)
