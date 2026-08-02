import os

from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
e = create_engine(url)
with e.connect() as c:
    print("modules:", c.execute(text("SELECT COUNT(*) FROM modules")).scalar())
    print("widgets:", c.execute(text("SELECT COUNT(*) FROM widgets")).scalar())
    print("org_modules:", c.execute(text("SELECT COUNT(*) FROM org_modules")).scalar())
    print(
        "dashboard set on",
        c.execute(text("SELECT COUNT(*) FROM modules WHERE dashboard IS NOT NULL")).scalar(),
        "modules",
    )
    rows = c.execute(
        text("SELECT key, dashboard FROM modules WHERE key IN ('sales','finance','meetings','settings') ORDER BY key")
    ).fetchall()
    for r in rows:
        print(" ", r[0], "->", r[1])
