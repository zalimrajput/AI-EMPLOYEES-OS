from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session


from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse
)

from app.services.organization_service import (
    create_organization
)


router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)



@router.post(
    "/",
    response_model=OrganizationResponse
)
def create(
    data:OrganizationCreate,
    db:Session=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    return create_organization(
        db,
        data,
        created_by=current_user.get("sub")
    )