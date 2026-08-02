from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1._crud import require_org_admin, require_org_member
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.organization_settings import OrganizationSettings


router = APIRouter(
    prefix="/organization-settings",
    tags=["Organization Settings"]
)


class OrgSettingsUpdate(BaseModel):
    company_name: str | None = None
    timezone: str | None = None
    language: str | None = None
    currency: str | None = None
    tax_rate: float | None = None
    invoice_prefix: str | None = None
    quotation_prefix: str | None = None
    date_format: str | None = None
    logo_url: str | None = None


class OrgSettingsOut(OrgSettingsUpdate):
    id: UUID
    organization_id: UUID

    model_config = {"from_attributes": True}


def _get_or_create(db: Session, organization_id) -> OrganizationSettings:
    settings = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == organization_id
    ).first()
    if settings is None:
        settings = OrganizationSettings(organization_id=organization_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/", response_model=OrgSettingsOut)
# Protected endpoint: returns (and creates on demand) the org's settings.
def get_settings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    return _get_or_create(db, me.organization_id)


@router.patch("/", response_model=OrgSettingsOut)
# Protected endpoint: org admin updates their organization's settings.
def update_settings(
    data: OrgSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    require_org_admin(db, me.id, me.organization_id)
    settings = _get_or_create(db, me.organization_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings
