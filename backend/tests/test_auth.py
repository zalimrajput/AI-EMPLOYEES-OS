"""Auth unit tests: token verification behavior without hitting the network.

Uses the local-HS256 path (SUPABASE_JWT_SECRET set) to build/verify tokens.
"""
import sys
import time

sys.path.insert(0, ".")

import pytest
from jose import jwt


@pytest.fixture(scope="module")
def local_auth():
    from app.core import auth

    old_secret = auth.settings.SUPABASE_JWT_SECRET
    old_alg = auth.settings.JWT_ALGORITHM
    auth.settings.SUPABASE_JWT_SECRET = "test-secret"
    auth.settings.JWT_ALGORITHM = "HS256"
    yield auth
    auth.settings.SUPABASE_JWT_SECRET = old_secret
    auth.settings.JWT_ALGORITHM = old_alg


def _make_token(secret, exp_offset=3600, aud="authenticated", sub="u1"):
    return jwt.encode(
        {"sub": sub, "aud": aud, "exp": time.time() + exp_offset},
        secret,
        algorithm="HS256",
    )


def test_valid_token(local_auth):
    claims = local_auth.verify_supabase_token(_make_token("test-secret"))
    assert claims["sub"] == "u1"


def test_expired_token(local_auth):
    with pytest.raises(Exception) as exc:
        local_auth.verify_supabase_token(_make_token("test-secret", exp_offset=-10))
    assert exc.value.status_code == 401


def test_malformed_token(local_auth):
    with pytest.raises(Exception) as exc:
        local_auth.verify_supabase_token("not.a.jwt")
    assert exc.value.status_code == 401


def test_wrong_secret(local_auth):
    with pytest.raises(Exception):
        local_auth.verify_supabase_token(_make_token("other-secret"))