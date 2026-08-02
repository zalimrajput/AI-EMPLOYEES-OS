"""Audit multi-tenant security of the live Supabase database.

Reads DATABASE_URL from backend/.env and reports:
- RLS coverage: every public table must have relrowsecurity = true
- Tables missing an RLS policy (policies with USING/WITH CHECK)
- Tables without an organization_id (or parent-FK tenancy) column
- Tables with RLS enabled but no policy (data is fully blocked -> also a bug)
- Grants summary per role
- FK columns lacking an index
- The current_org_id() helper existence
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

        # 1. All public tables + RLS status
        q(
            "RLS coverage (expect ALL true)",
            """
            SELECT c.relname AS table_name, c.relrowsecurity AS rls_enabled
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
              AND c.relname <> 'schema_migrations'
            ORDER BY c.relname
            """,
        )

        # 2. Tables with RLS enabled but ZERO policies -> data inaccessible
        q(
            "RLS ON but no policy (data fully blocked)",
            """
            SELECT c.relname AS table_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
              AND c.relrowsecurity = true
              AND c.relname <> 'schema_migrations'
              AND NOT EXISTS (
                SELECT 1 FROM pg_policies p
                WHERE p.schemaname = 'public' AND p.tablename = c.relname
              )
            ORDER BY c.relname
            """,
        )

        # 3. Tables with RLS OFF -> fully exposed (critical)
        q(
            "RLS OFF tables (CRITICAL - exposed)",
            """
            SELECT c.relname AS table_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
              AND c.relrowsecurity = false
              AND c.relname <> 'schema_migrations'
            ORDER BY c.relname
            """,
        )

        # 4. Tables missing organization_id and no parent-FK tenancy path
        q(
            "Tables without organization_id column",
            """
            SELECT c.relname AS table_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
              AND c.relname <> 'schema_migrations'
              AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns ic
                WHERE ic.table_schema = 'public'
                  AND ic.table_name = c.relname
                  AND ic.column_name = 'organization_id'
              )
            ORDER BY c.relname
            """,
        )

        # 5. current_org_id helper
        q(
            "current_org_id() helper exists",
            """
            SELECT p.proname, pg_get_function_identity_arguments(p.oid) AS args
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'public' AND p.proname = 'current_org_id'
            """,
        )

        # 6. FK columns without an index (slow cross-tenant joins / locks)
        q(
            "FK columns without index",
            """
            SELECT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND NOT EXISTS (
                SELECT 1 FROM pg_index i
                JOIN pg_class ic ON ic.oid = i.indrelid
                JOIN pg_namespace ni ON ni.oid = ic.relnamespace
                JOIN pg_attribute a
                  ON a.attrelid = i.indrelid AND a.attnum = ANY (i.indkey)
                WHERE ni.nspname = 'public'
                  AND ic.relname = tc.table_name
                  AND a.attname = kcu.column_name
              )
            ORDER BY tc.table_name, kcu.column_name
            """,
        )

        # 7. Grants summary
        q(
            "Grants per role",
            """
            SELECT grantee, count(*) AS privilege_count
            FROM information_schema.role_table_grants
            WHERE table_schema = 'public'
            GROUP BY grantee ORDER BY grantee
            """,
        )

        # 8. Table count
        q(
            "Total public tables",
            """
            SELECT count(*) FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
              AND c.relname <> 'schema_migrations'
            """,
        )

        # 9. Sample of policies by table (to eyeball USING expressions)
        q(
            "Policies (table, name, cmd, roles)",
            """
            SELECT tablename, policyname, cmd, roles
            FROM pg_policies
            WHERE schemaname = 'public'
            ORDER BY tablename, cmd
            """,
        )


if __name__ == "__main__":
    main()
