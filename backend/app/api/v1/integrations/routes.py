from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1._crud import crud_router, require_org_member
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.integration import Integration
from app.services.integration_service import (
    build_authorize_url,
    disconnect,
    exchange_code,
    get_provider_config,
    save_credentials,
)


router = APIRouter()


router.include_router(
    crud_router(
        Integration,
        prefix="/integrations",
        tags=["Integrations"],
        search_fields=["provider"],
    )
)


@router.get("/integrations/oauth/connect/{provider}", tags=["Integrations"])
# Protected endpoint: returns the provider authorization URL to redirect to.
def oauth_start(
    provider: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    if get_provider_config(provider) is None:
        raise HTTPException(status_code=400, detail="Provider not configured")
    state = f"{me.organization_id}:{token_urlsafe(16)}"
    try:
        return {"authorize_url": build_authorize_url(provider, state)}
    except ValueError:
        raise HTTPException(status_code=400, detail="Provider not configured")


@router.get("/integrations/oauth/callback/{provider}", tags=["Integrations"])
# Public callback: exchanges the provider code and stores encrypted tokens.
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    error: str | None = Query(None),
    db: Session = Depends(get_db),
):
    if error:
        raise HTTPException(status_code=400, detail=f"Provider error: {error}")
    try:
        org_id = state.split(":", 1)[0]
    except (ValueError, IndexError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid state")
    try:
        tokens = await exchange_code(provider, code)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    row = save_credentials(db, org_id, provider, tokens)
    return {
        "connected": True,
        "provider": provider,
        "integration_id": str(row.id),
    }