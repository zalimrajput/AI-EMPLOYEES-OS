from contextvars import ContextVar



current_user = ContextVar(
    "current_user",
    default=None
)



current_organization = ContextVar(
    "current_organization",
    default=None
)