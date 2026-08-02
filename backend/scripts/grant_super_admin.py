"""Grant the Super Admin platform role to an existing user (idempotent)."""
import os
import sys

from sqlalchemy import create_engine, text

EMAIL = "rkmeer6692@gmail.com"
ROLE = "Super Admin"

url = os.environ.get("DATABASE_URL")
e = create_engine(url)
with e.connect() as c:
    row = c.execute(
        text("SELECT id, email FROM auth.users WHERE email = :email"),
        {"email": EMAIL},
    ).fetchone()
    if row is None:
        print(f"ERROR: no auth user with email {EMAIL}")
        sys.exit(1)
    user_id = row[0]
    print("found user:", row[1], "| id:", user_id)

    existing = c.execute(
        text("SELECT id, role FROM platform_roles WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchall()
    for r in existing:
        print("already has platform role:", r[1])

    if not existing:
        c.execute(
            text(
                "INSERT INTO platform_roles (user_id, role) VALUES (:uid, :role)"
            ),
            {"uid": user_id, "role": ROLE},
        )
        c.commit()
        print(f"GRANTED: {ROLE} -> {EMAIL}")

    # Confirm
    rows = c.execute(text("SELECT user_id, role FROM platform_roles")).fetchall()
    print("--- platform_roles now ---")
    for r in rows:
        print(" ", r[0], "|", r[1])
