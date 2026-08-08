"""Request-scoped context variables.

These are only ever written by the authentication / tenant resolvers and read
by observability middleware.  They are intentionally not used as an access
control mechanism by themselves — every query is explicitly scoped to the
caller's ``organization_id`` in addition to Postgres RLS.
"""
from contextvars import ContextVar
from uuid import UUID
from typing import Optional

current_user: ContextVar[Optional[dict]] = ContextVar("current_user", default=None)

current_organization: ContextVar[Optional[dict]] = ContextVar(
    "current_organization", default=None
)

current_org_id: ContextVar[Optional[UUID]] = ContextVar("current_org_id", default=None)