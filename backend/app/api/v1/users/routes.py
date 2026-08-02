from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserCreate
from app.services.user_service import create_user, delete_user, list_org_users


# Roles that may administer an organization (create/delete members).
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
            detail="Only organization admins can manage members"
        )


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/")
# Protected endpoint: requires a valid Supabase token.
# Admin operation - creates a Supabase Auth user and assigns an org.
# End users sign up via the frontend (supabase.auth.signUp), which is public.
def register_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    me = db.query(User).filter(User.id == current_user.get("sub")).first()
    if me is None or me.organization_id is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of any organization"
        )
    if str(me.organization_id) != str(data.organization_id):
        raise HTTPException(
            status_code=403,
            detail="You can only add members to your own organization"
        )
    _require_org_admin(db, me.id, me.organization_id)
    try:
        user = create_user(
            db,
            data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    return user


@router.get("/")
# Protected endpoint: lists all users of the caller's organization.
def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from app.models.user import User

    me = db.query(User).filter(User.id == current_user.get("sub")).first()
    if me is None or me.organization_id is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of any organization"
        )
    return list_org_users(db, me.organization_id)


@router.delete("/{user_id}")
# Protected endpoint: org admin deletes a user from their organization.
def remove_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    me = db.query(User).filter(User.id == current_user.get("sub")).first()
    if me is None or me.organization_id is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of any organization"
        )
    _require_org_admin(db, me.id, me.organization_id)
    if user_id == me.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account"
        )
    try:
        return delete_user(db, user_id, me.organization_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
