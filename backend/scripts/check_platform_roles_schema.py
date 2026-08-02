"""Check platform_roles schema + existing users on the live DB."""
import os
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
e = create_engine(url)
with e.connect() as c:
    print("--- platform_roles columns ---")
    for col in c.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name='platform_roles' ORDER BY ordinal_position"
    )).fetchall():
        print(" ", col[0], col[1])
    print("--- auth users (last 5) ---")
    try:
        rows = c.execute(text(
            "SELECT id, email, created_at FROM auth.users "
            "ORDER BY created_at DESC LIMIT 5"
        )).fetchall()
        for r in rows:
            print(" ", r[1], "|", r[2])
    except Exception as ex:
        print("  err:", str(ex).split("\n")[0][:80])
    print("--- users table (last 5) ---")
    rows = c.execute(text(
        "SELECT id, email, full_name, organization_id FROM users "
        "ORDER BY created_at DESC LIMIT 5"
    )).fetchall()
    for r in rows:
        print(" ", r[1], "|", r[2], "| org:", r[3])
