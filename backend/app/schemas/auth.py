from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    roles: list[str] = []
    is_super_admin: bool = False
    status: Optional[str] = None