from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.module import ModuleOut, OrgModuleOut, OrgModuleUpdate
from app.services.module_service import (
    get_user_organization_id,
    is_org_admin,
    is_super_admin,
    list_modules_with_widgets,
    list_org_modules,
    update_org_admin_module,
    update_super_admin_module,
)


router = APIRouter(
    prefix="/modules",
    tags=["Modules"]
)


def _require_super_admin(db: Session, current_user: dict) -> None:
    if not is_super_admin(db, current_user.get("sub")):
        raise HTTPException(
            status_code=403,
            detail="Platform super admin access required"
        )


def _require_org_admin(db: Session, current_user: dict, organization_id) -> None:
    if not is_org_admin(db, current_user.get("sub"), organization_id):
        raise HTTPException(
            status_code=403,
            detail="Only organization admins can manage modules"
        )


@router.get("/", response_model=list[ModuleOut])
# Protected: any authenticated user may read the module catalog.
def list_modules(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return list_modules_with_widgets(db)


@router.get("/org/{organization_id}", response_model=list[OrgModuleOut])
# Protected: org admin of that org, or the platform Super Admin (who can
# inspect any company's module setup) reads module settings.
def get_org_modules(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not is_super_admin(db, current_user.get("sub")):
        _require_org_admin(db, current_user, organization_id)
    return list_org_modules(db, organization_id)


@router.patch("/org/{organization_id}/{module_key}", response_model=OrgModuleOut)
# Protected: Super Admin toggles a module for any organization.
def patch_super_admin_module(
    organization_id: UUID,
    module_key: str,
    data: OrgModuleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    _require_super_admin(db, current_user)
    if data.enabled_by_super_admin is None:
        raise HTTPException(
            status_code=400,
            detail="enabled_by_super_admin is required"
        )
    return update_super_admin_module(
        db,
        organization_id,
        module_key,
        data.enabled_by_super_admin,
    )


@router.patch("/me/{module_key}", response_model=OrgModuleOut)
# Protected: Org Admin toggles a module for their own workspace.
def patch_my_module(
    module_key: str,
    data: OrgModuleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    org_id = get_user_organization_id(db, current_user.get("sub"))
    if org_id is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of any organization"
        )
    _require_org_admin(db, current_user, org_id)
    if data.enabled_by_org_admin is None:
        raise HTTPException(
            status_code=400,
            detail="enabled_by_org_admin is required"
        )
    try:
        return update_org_admin_module(
            db,
            org_id,
            module_key,
            data.enabled_by_org_admin,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
