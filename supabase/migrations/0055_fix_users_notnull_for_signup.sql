-- 0055_fix_users_notnull_for_signup.sql
-- The live `users` table has email/password_hash columns (NOT NULL) that are
-- NOT defined in migration 0003 — they were added outside migrations (drift).
-- The handle_new_user() signup trigger inserts a row without email/password_hash,
-- which violates those NOT NULL constraints (error 23502) and breaks signup.
--
-- Fix: make them nullable. Supabase Auth is the source of truth for credentials;
-- the backend's legacy create_user() flow can still populate them when used.
-- This unblocks GoTrue signup while keeping existing flows working.

ALTER TABLE users ALTER COLUMN email DROP NOT NULL;
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;
