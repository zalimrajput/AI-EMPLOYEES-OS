import httpx

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

from app.core.config import settings


bearer_scheme = HTTPBearer(
    auto_error=False
)


def verify_supabase_token(
    token: str
) -> dict:
    """Verify a Supabase-issued access token and return its claims.

    Primary path: local HS256 verification using SUPABASE_JWT_SECRET
    (audience ``authenticated``) — fast and offline.

    Fallback: if SUPABASE_JWT_SECRET is not configured yet, validate the token
    server-side against GoTrue (GET /auth/v1/user). This keeps protected
    endpoints working out of the box; set SUPABASE_JWT_SECRET in .env to enable
    local verification.
    """
    if settings.SUPABASE_JWT_SECRET:
        try:
            return jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    url = f"{settings.SUPABASE_URL}/auth/v1/user"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {token}",
    }
    try:
        resp = httpx.get(
            url,
            headers=headers,
            timeout=20
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=503,
            detail="Auth service unavailable"
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    data = resp.json()
    return {
        "sub": data.get("id"),
        "email": data.get("email"),
        "aud": "authenticated",
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    )
) -> dict:
    """FastAPI dependency: require a valid Supabase access token.

    Returns the verified JWT claims (use ``claims["sub"]`` for the user id).
    Raises 401 when the Authorization header is missing or the token is
    invalid/expired.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    return verify_supabase_token(
        credentials.credentials
    )
