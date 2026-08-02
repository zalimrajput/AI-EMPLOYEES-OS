from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.activity import Activity
from app.models.customer import Customer
from app.models.lead import Lead
from app.models.pipeline import Deal, Pipeline
from app.models.reminder import Reminder


router = APIRouter()


router.include_router(
    crud_router(
        Customer,
        prefix="/customers",
        tags=["CRM"],
        search_fields=["name", "email", "company", "phone"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        Lead,
        prefix="/leads",
        tags=["CRM"],
        search_fields=["name", "email", "company"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        Pipeline,
        prefix="/pipelines",
        tags=["CRM"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        Deal,
        prefix="/deals",
        tags=["CRM"],
        search_fields=["title"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        Activity,
        prefix="/activities",
        tags=["CRM"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        Reminder,
        prefix="/reminders",
        tags=["CRM"],
        write_scope="member",
    )
)
