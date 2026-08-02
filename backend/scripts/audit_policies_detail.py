"""Deep policy audit for the live Supabase DB.

Uses pg_policy directly (the pg_policies view doesn't expose polrelid) to
inspect USING/WITH CHECK expressions and the roles each policy applies to.

Focus areas:
- Policies that apply to ALL roles (polroles = {}) — anon can hit them.
- USING expressions on the 5 tables without organization_id.
- anon table grants.
"""
import os
import sys

from sqlalchemy import create_engine, text


def load_env(path):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    load_env(os.path.join(os.path.dirname(__file__), "..", ".env"))
    url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if not url:
        print("NO_DB_URL")
        sys.exit(1)

    engine = create_engine(url)
    with engine.connect() as conn:
        def q(label, sql):
            try:
                rows = conn.execute(text(sql)).fetchall()
                print(f"\n== {label} ({len(rows)} rows) ==")
                for r in rows:
                    print("  " + " | ".join(str(x) for x in r))
                return rows
            except Exception as exc:  # noqa: BLE001
                print(f"\n== {label} == ERROR {type(exc).__name__}: {exc}")
                return []

        # All policies with role names resolved, USING and WITH CHECK.
        q(
            "All policies (roles, cmd, USING, WITH CHECK)",
            """
            SELECT
                n.nspname AS schema,
                c.relname AS table_name,
                pol.polname AS policy_name,
                CASE pol.polcmd
                    WHEN 'r' THEN 'SELECT' WHEN 'a' THEN 'INSERT'
                    WHEN 'w' THEN 'UPDATE' WHEN 'd' THEN 'DELETE'
                    ELSE 'ALL' END AS cmd,
                CASE WHEN pol.polroles = ARRAY[]::oid[]
                    THEN '(all roles)' ELSE (
                        SELECT string_agg(r.rolname, ',')
                        FROM pg_roles r WHERE r.oid = ANY (pol.polroles)
                    ) END AS roles,
                pg_get_expr(pol.polqual, pol.polrelid) AS using_expr,
                pg_get_expr(pol.polwithcheck, pol.polrelid) AS with_check_expr
            FROM pg_policy pol
            JOIN pg_class c ON c.oid = pol.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
            ORDER BY c.relname, pol.polname
            """,
        )

        # Policies that apply to ALL roles (incl. anon).
        q(
            "Policies applying to ALL roles (incl. anon)",
            """
            SELECT
                c.relname AS table_name,
                pol.polname AS policy_name,
                CASE pol.polcmd
                    WHEN 'r' THEN 'SELECT' WHEN 'a' THEN 'INSERT'
                    WHEN 'w' THEN 'UPDATE' WHEN 'd' THEN 'DELETE'
                    ELSE 'ALL' END AS cmd,
                pg_get_expr(pol.polqual, pol.polrelid) AS using_expr
            FROM pg_policy pol
            JOIN pg_class c ON c.oid = pol.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND pol.polroles = ARRAY[]::oid[]
            ORDER BY c.relname, pol.polname
            """,
        )

        # Policies on the 5 non-org tables.
        q(
            "Policies on non-org tables",
            """
            SELECT
                c.relname AS table_name,
                pol.polname AS policy_name,
                CASE pol.polcmd
                    WHEN 'r' THEN 'SELECT' WHEN 'a' THEN 'INSERT'
                    WHEN 'w' THEN 'UPDATE' WHEN 'd' THEN 'DELETE'
                    ELSE 'ALL' END AS cmd,
                CASE WHEN pol.polroles = ARRAY[]::oid[]
                    THEN '(all roles)' ELSE (
                        SELECT string_agg(r.rolname, ',')
                        FROM pg_roles r WHERE r.oid = ANY (pol.polroles)
                    ) END AS roles,
                pg_get_expr(pol.polqual, pol.polrelid) AS using_expr
            FROM pg_policy pol
            JOIN pg_class c ON c.oid = pol.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname IN
                ('organizations', 'plans', 'platform_roles',
                 'platform_settings', 'platform_logs')
            ORDER BY c.relname, pol.polname
            """,
        )

        # anon grants by table (grant alone isn't enough — RLS is the gate).
        q(
            "anon grants by table",
            """
            SELECT table_name, string_agg(privilege_type, ',' ORDER BY privilege_type) AS privs
            FROM information_schema.role_table_grants
            WHERE table_schema = 'public' AND grantee = 'anon'
            GROUP BY table_name ORDER BY table_name
            """,
        )

        # Count of policies per table (sanity: every tenant table has >= 1).
        q(
            "Policy count per table",
            """
            SELECT c.relname AS table_name, count(pol.oid) AS policy_count
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_policy pol ON pol.polrelid = c.oid
            WHERE n.nspname = 'public' AND c.relkind = 'r'
              AND c.relname <> 'schema_migrations'
            GROUP BY c.relname
            ORDER BY c.relname
            """,
        )


if __name__ == "__main__":
    main()
