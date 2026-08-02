"""Check the plans table schema + rows on the live Supabase DB."""
import os
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
e = create_engine(url)
with e.connect() as c:
    print("--- plans columns ---")
    cols = c.execute(
        text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name='plans' ORDER BY ordinal_position"
        )
    ).fetchall()
    for col in cols:
        print(" ", col[0], col[1])
    print("--- plans rows ---")
    for r in c.execute(text("SELECT * FROM plans ORDER BY created_at LIMIT 6")).fetchall():
        print(" ", r)
