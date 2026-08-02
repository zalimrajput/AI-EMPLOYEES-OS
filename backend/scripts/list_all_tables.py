"""List every public table in the live Supabase DB."""
import os
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
e = create_engine(url)
with e.connect() as c:
    print("--- ALL public tables ---")
    rows = c.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name"
        )
    ).fetchall()
    for r in rows:
        print(" ", r[0])
