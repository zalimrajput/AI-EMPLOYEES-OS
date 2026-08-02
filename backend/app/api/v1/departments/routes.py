from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.department import DepartmentCreate, DepartmentOut
from app.services.department_service import (
    create_department,
    delete_department,
    list_org_departments,
)


# Roles that may administer an organization (create/delete departments).
ADMIN_ROLE_NAMES = {"Company Admin", "CEO / Executive", "Owner", "Admin"}


def _require_org_admin(
    db: Session,
    user_id,
    organization_id
) -> None:
    """Raise 403 unless the user holds an org-admin role for the organization."""
    is_admin = db.query(UserRole).join(
        Role, UserRole.role_id == Role.id
    ).filter(
        UserRole.user_id == user_id,
        UserRole.organization_id == organization_id,
        Role.name.in_(ADMIN_ROLE_NAMES),
    ).first()
    if is_admin is None:
        raise HTTPException(
            status_code=403,
            detail="Only organization admins can manage departments"
        )


def _require_org_member(
    db: Session,
    current_user: dict,
):
    """Resolve the caller's user row; raise 403 unless they belong to an org."""
    me = db.query(User).filter(User.id == current_user.get("sub")).first()
    if me is None or me.organization_id is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of any organization"
        )
    return me


router = APIRouter(
    prefix="/departments",
    tags=["Departments"]
)


@router.get("/", response_model=list[DepartmentOut])
# Protected endpoint: lists all departments of the caller's organization.
def list_departments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    me = _require_org_member(db, current_user)
    return list_org_departments(db, me.organization_id)


@router.post("/", response_model=DepartmentOut, status_code=201)
# Protected endpoint: org admin creates a department in their own organization.
def create_department_route(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    me = _require_org_member(db, current_user)
    _require_org_admin(db, me.id, me.organization_id)
    try:
        return create_department(
            db,
            me.organization_id,
            data.name,
            data.description,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.delete("/{department_id}")
# Protected endpoint: org admin deletes a department from their organization.
def remove_department(
    department_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    me = _require_org_member(db, current_user)
    _require_org_admin(db, me.id, me.organization_id)
    try:
        return delete_department(
            db,
            department_id,
            me.organization_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
