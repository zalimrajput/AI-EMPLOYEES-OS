-- 0058_drop_users_email_unique.sql
-- The signup trigger (0057) now copies email from auth.users into
-- public.users.email. Supabase Auth already enforces email uniqueness, so the
-- leftover UNIQUE(email) constraint on public.users is redundant AND risky:
-- legacy rows (created by the old local-auth flow) may already hold an email
-- that later signs up via Supabase, which would make the trigger's INSERT
-- violate users_email_key and break that signup with a 500.
--
-- Drop it — Supabase Auth is the single source of truth for email uniqueness.
ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_email_key;
