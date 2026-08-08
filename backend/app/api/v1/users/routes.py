from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1._crud import require_org_admin, require_org_member
from app.core.auth import get_current_user
from app.core.database import get_db
from app.schemas.user import UserCreate
from app.services.user_service import create_user, delete_user, list_org_users


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post("/")
# Protected endpoint: requires a valid Supabase token.
# Admin operation - creates a Supabase Auth user and assigns an org.
# End users sign up via the frontend (supabase.auth.signUp), which is public.
def register_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    if str(me.organization_id) != str(data.organization_id):
        raise HTTPException(
            status_code=403,
            detail="You can only add members to your own organization",
        )
    require_org_admin(db, me.id, me.organization_id)
    try:
        return create_user(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
# Protected endpoint: lists all users of the caller's organization.
def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    return list_org_users(db, me.organization_id)


@router.delete("/{user_id}")
# Protected endpoint: org admin deletes a user from their organization.
def remove_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    require_org_admin(db, me.id, me.organization_id)
    if user_id == me.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account",
        )
    try:
        return delete_user(db, user_id, me.organization_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))