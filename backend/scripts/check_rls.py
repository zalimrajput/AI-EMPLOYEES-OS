"""Check RLS enabled + policies for ai_employees and integrations on live DB."""
import os
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
e = create_engine(url)
with e.connect() as c:
    for t in ["ai_employees", "integrations", "dashboards"]:
        print(f"--- {t} ---")
        row = c.execute(
            text(
                "SELECT relrowsecurity, relforcerowsecurity "
                "FROM pg_class WHERE relname = :t"
            ),
            {"t": t},
        ).fetchone()
        print("  RLS enabled:", row[0] if row else "table missing")
        pols = c.execute(
            text(
                "SELECT policyname, cmd, qual, with_check "
                "FROM pg_policies WHERE tablename = :t"
            ),
            {"t": t},
        ).fetchall()
        if not pols:
            print("  no policies")
        for p in pols:
            print("  policy:", p[0], "|", p[1], "|", (p[2] or "")[:60], "|", (p[3] or "")[:60])
