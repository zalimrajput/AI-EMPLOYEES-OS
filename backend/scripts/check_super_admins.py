"""Find existing Super Admin users on the live DB."""
import os
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
e = create_engine(url)
with e.connect() as c:
    print("--- platform_roles rows ---")
    rows = c.execute(text("SELECT * FROM platform_roles")).fetchall()
    for r in rows:
        print(" ", r)
    if not rows:
        print("  (none — no super admin assigned yet)")
    print("--- users with those ids ---")
    for r in rows:
        cols = [c_ for c_ in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='users'"
        )).fetchall()]
        colnames = [x[0] for x in cols]
        uid_col = [x for x in colnames if "id" in x]
        uid = getattr(r, "_mapping", None)
        # r is a Row; find the user_id column
        keys = list(r._mapping.keys())
        user_id = None
        for k in keys:
            if "user" in k.lower() and "id" in k.lower():
                user_id = r._mapping[k]
        if not user_id:
            continue
        u = c.execute(
            text("SELECT email, full_name, organization_id FROM users WHERE id = :uid"),
            {"uid": user_id},
        ).fetchone()
        if u:
            print("  email:", u[0], "| name:", u[1], "| org:", u[2])
