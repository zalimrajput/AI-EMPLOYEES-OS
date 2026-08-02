-- 0053_org_creation_and_self_update.sql
-- Runtime fixes flagged during review:
--  1) Allow an authenticated user to create an organization (auto-assigns them).
--  2) Allow a user (even org-less) to update their own profile.
--  3) Neutral display-name fallback in the signup trigger.

-- (1) Org creation: authenticated user can INSERT an org; trigger binds them.
CREATE OR REPLACE FUNCTION public.set_org_creator()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    UPDATE public.users
    SET organization_id = NEW.id
    WHERE id = auth.uid()
      AND organization_id IS NULL;
    RETURN NEW;
END;
$$;

DROP POLICY IF EXISTS organizations_create ON organizations;
CREATE POLICY organizations_create ON organizations
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

DROP TRIGGER IF EXISTS trg_set_org_creator ON organizations;
CREATE TRIGGER trg_set_org_creator
    AFTER INSERT ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION public.set_org_creator();

-- (2) User self-update (covers org-less users; tenant policy still governs
--     updating OTHER users in the org).
DROP POLICY IF EXISTS users_self_update ON users;
CREATE POLICY users_self_update ON users
    FOR UPDATE
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- (3) Neutral fallback instead of storing the email as the display name.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.users (id, full_name, avatar_url, status)
    VALUES (
        NEW.id,
        COALESCE(NULLIF(NEW.raw_user_meta_data->>'full_name', ''), NEW.raw_user_meta_data->>'name', 'New User'),
        NEW.raw_user_meta_data->>'avatar_url',
        'active'
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
