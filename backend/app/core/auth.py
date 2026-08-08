"""Supabase JWT verification.

Authentication is exclusively based on Supabase-issued access tokens.  The
backend never hashes passwords, never issues its own JWTs and never stores
credentials in ``public`` tables.

Two verification paths exist:

1. ``SUPABASE_JWT_SECRET`` is set → offline HS256 verification against the
   secret (audience ``authenticated``).  Fast, no network dependency, and the
   default in production.
2. ``SUPABASE_JWT_SECRET`` is empty → server-side validation against GoTrue
   (``GET /auth/v1/user``). Kept so local/dev installs without the secret still
   work; it always makes a network round trip to confirm the token is live.

Only path 1 vs path 2 is logged — never the token itself.
"""
import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.core.config import settings
from app.core.logging import get_logger
from app.middleware.request_context import current_user

logger = get_logger("auth")

bearer_scheme = HTTPBearer(auto_error=False)


class AuthError(HTTPException):
    """Raised for any auth failure with a consistent 401 payload."""

    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(status_code=401, detail=detail)


def verify_supabase_token(token: str) -> dict:
    """Verify a Supabase-issued access token and return its claims."""
    if settings.SUPABASE_JWT_SECRET:
        try:
            claims = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                audience="authenticated",
            )
            logger.info("auth verification=local_hs256")
            return dict(claims)
        except ExpiredSignatureError:
            logger.info("auth verification=local_hs256 expired_token")
            raise AuthError("Token has expired")
        except JWTError:
            logger.info("auth verification=local_hs256 malformed_token")
            raise AuthError("Invalid token")

    url = f"{settings.SUPABASE_URL}/auth/v1/user"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {token}",
    }
    try:
        resp = httpx.get(url, headers=headers, timeout=20)
    except httpx.HTTPError:
        logger.error("auth verification=go_true unavailable")
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    if resp.status_code != 200:
        logger.info("auth verification=go_true invalid_token")
        raise AuthError("Invalid token")

    logger.info("auth verification=go_true")
    data = resp.json()
    return {
        "sub": data.get("id"),
        "email": data.get("email"),
        "aud": "authenticated",
        "app_metadata": data.get("app_metadata"),
        "user_metadata": data.get("user_metadata"),
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency: require a valid Supabase access token.

    Returns the verified JWT claims (user id is ``claims["sub"]``). Raises 401
    when the Authorization header is missing or the token is invalid/expired.
    """
    if credentials is None or not credentials.credentials:
        raise AuthError("Not authenticated")

    claims = verify_supabase_token(credentials.credentials)
    current_user.set(claims)
    return claims


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """FastAPI dependency: like get_current_user but returns just the user id."""
    return get_current_user(credentials).get("sub")