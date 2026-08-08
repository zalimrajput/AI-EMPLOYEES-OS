from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.organization import Organization
from app.models.platform import PlatformRole
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse
from app.services.auth_service import login_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    return login_user(data.email, data.password)


@router.get("/me", response_model=MeResponse)
# Protected endpoint: returns the verified caller's profile, org and roles.
# NOTE: works even when the user has not joined an organization yet, so the
# register flow can call it immediately after creating a workspace.
def me(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.get("sub")).first()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found for authenticated user",
        )

    roles = sorted(
        {
            ur.role.name
            for ur in user.user_roles
            if ur.role is not None
        }
    )

    org_name = None
    if user.organization_id is not None:
        org = db.query(Organization).filter(
            Organization.id == user.organization_id
        ).first()
        org_name = org.name if org else None

    is_super_admin = (
        db.query(PlatformRole)
        .filter(PlatformRole.user_id == user.id)
        .first()
        is not None
    )

    return MeResponse(
        id=str(user.id),
        email=user.email or current_user.get("email"),
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        organization_id=str(user.organization_id) if user.organization_id else None,
        organization_name=org_name,
        roles=sorted(roles),
        is_super_admin=is_super_admin,
        status=user.status,
    )