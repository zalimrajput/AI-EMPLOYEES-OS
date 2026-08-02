-- Generates CREATE INDEX statements for FK/tenancy columns without indexes.
-- Run with:  psql ... -f this.sql
SELECT
    'CREATE INDEX IF NOT EXISTS idx_' || tc.table_name || '_' || kcu.column_name
    || ' ON public.' || tc.table_name || '(' || kcu.column_name || ');' AS ddl
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
ORDER BY tc.table_name, kcu.column_name;

-- Confirm organizations.created_by exists (policy references it).
SELECT column_name FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'organizations'
  AND column_name IN ('created_by', 'id', 'name', 'slug');
