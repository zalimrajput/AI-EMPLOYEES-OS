import httpx

from fastapi import HTTPException

from app.core.config import settings


def login_user(
    email: str,
    password: str
):
    """Authenticate against Supabase Auth (GoTrue) and return its tokens.

    Supabase Auth is the single source of truth for credentials - no local
    password hashes are stored or verified by this application.
    """
    url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        "password": password,
    }

    try:
        resp = httpx.post(
            url,
            json=payload,
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
            detail="Invalid email or password"
        )

    data = resp.json()

    return {
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "token_type": "bearer",
    }
