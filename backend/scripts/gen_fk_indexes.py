"""Generate CREATE INDEX DDL for FK/tenancy columns missing indexes on the live DB."""
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
        rows = conn.execute(
            text(
                """
                SELECT DISTINCT tc.table_name, kcu.column_name
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
                """
            )
        ).fetchall()

        print(f"-- {len(rows)} FK columns missing an index\n")
        for table, col in rows:
            print(f"CREATE INDEX IF NOT EXISTS idx_{table}_{col} ON public.{table}({col});")

        # Confirm organizations.created_by
        created_by = conn.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'organizations'
                  AND column_name = 'created_by'
                """
            )
        ).scalar()
        print(f"\n-- organizations.created_by exists: {bool(created_by)}")


if __name__ == "__main__":
    main()
