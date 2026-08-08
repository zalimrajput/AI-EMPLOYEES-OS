from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1._crud import require_org_admin, require_org_member
from app.core.auth import get_current_user
from app.core.database import get_db
from app.schemas.department import (
    DepartmentCreate,
    DepartmentOut,
    DepartmentPatch,
)
from app.services.department_service import (
    create_department,
    delete_department,
    get_department,
    list_org_departments,
    update_department,
)


router = APIRouter(
    prefix="/departments",
    tags=["Departments"],
)


@router.get("/", response_model=list[DepartmentOut])
# Protected endpoint: lists all departments of the caller's organization.
def list_departments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    return list_org_departments(db, me.organization_id)


@router.post("/", response_model=DepartmentOut, status_code=201)
# Protected endpoint: org admin creates a department in their own organization.
def create_department_route(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    require_org_admin(db, me.id, me.organization_id)
    try:
        return create_department(
            db,
            me.organization_id,
            data.name,
            data.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{department_id}", response_model=DepartmentOut)
# Protected endpoint: reads one department of the caller's organization.
def get_department_route(
    department_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    try:
        return get_department(db, department_id, me.organization_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{department_id}", response_model=DepartmentOut)
# Protected endpoint: org admin updates a department in their organization.
def update_department_route(
    department_id: UUID,
    data: DepartmentPatch,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    require_org_admin(db, me.id, me.organization_id)
    try:
        return update_department(
            db,
            department_id,
            me.organization_id,
            name=data.name,
            description=data.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{department_id}")
# Protected endpoint: org admin deletes a department from their organization.
def remove_department(
    department_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    require_org_admin(db, me.id, me.organization_id)
    try:
        return delete_department(
            db,
            department_id,
            me.organization_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))