"""SQLAlchemy session management.

Decision (documented in the Phase 1 report): the application database layer is
**synchronous** on ``psycopg2``.  The whole existing codebase (``_crud.py``,
all services, all routers) is built around sync ``Session``, and async would
have forced a rewrite of every layer for negligible benefit at this workload.
AI streaming is handled separately with ``httpx``/``StreamingResponse`` and
never blocks a worker thread.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Normalize the URL so "postgres://" / "postgresql://" always resolve to the
# psycopg2 driver we ship (never depend on the scheme implying a driver).
_database_url = settings.DATABASE_URL
if _database_url.startswith("postgres://"):
    _database_url = _database_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif _database_url.startswith("postgresql://"):
    _database_url = _database_url.replace(
        "postgresql://", "postgresql+psycopg2://", 1
    )

engine = create_engine(
    _database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """FastAPI dependency: yield a scoped session, always closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()