-- 0037_grants.sql
-- Grant database access to Supabase roles so the app can read/write data.
-- (Without these, anon/authenticated can access nothing.)

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

-- anon: read-only on everything (RLS still filters rows per-user)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- authenticated: full CRUD on tenant tables (RLS enforces isolation)
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;

-- service_role: full access, bypasses RLS
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;

-- Future tables inherit these defaults
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role;
