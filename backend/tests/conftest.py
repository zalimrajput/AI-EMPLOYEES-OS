"""Pytest fixtures: path setup + DB availability detection.

The suite is split into:
- pure unit tests (engine loop, agents, guardrails, chunking) that never touch
  a database and always run;
- API tests that use the live Postgres configured in ``env``/``.env`` and are
  skipped automatically when the database is unreachable (CI without Postgres).
"""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import pytest


def db_available() -> bool:
    try:
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _db() -> bool:
    return db_available()


DB_AVAILABLE = _db()


def pytest_collection_modifyitems(config, items):
    """Skip API/db tests early when Postgres is unavailable."""
    if DB_AVAILABLE:
        return
    for item in items:
        if "db" in item.keywords or "api" in item.keywords:
            item.add_marker(
                pytest.mark.skip(reason="database unavailable; skipping db tests")
            )


@pytest.fixture()
def db():
    if not DB_AVAILABLE:
        pytest.skip("database unavailable")
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()