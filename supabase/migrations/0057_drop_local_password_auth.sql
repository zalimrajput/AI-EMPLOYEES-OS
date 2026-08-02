-- 0057_drop_local_password_auth.sql
-- Local password authentication is removed. Supabase Auth (auth.users) is the
-- single source of truth for credentials; public.users is a profile table.
--
-- 1) Drop the drifted password_hash column (local bcrypt storage).
ALTER TABLE public.users DROP COLUMN IF EXISTS password_hash;

-- 2) Keep public.users.email in sync with auth.users for display/API use
--    (email remains NULL only for legacy rows that predate the trigger).
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.users (id, full_name, email, avatar_url, status)
    VALUES (
        NEW.id,
        COALESCE(NULLIF(NEW.raw_user_meta_data->>'full_name', ''), NEW.raw_user_meta_data->>'name', 'New User'),
        NEW.email,
        NEW.raw_user_meta_data->>'avatar_url',
        'active'
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;
