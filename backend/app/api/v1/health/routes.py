from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine


router = APIRouter()


@router.get("/")
def health():

    database_status = "disconnected"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            database_status = "connected"

    except Exception as e:
        database_status = str(e)

    return {
        "status": "ok",
        "database": database_status
    }