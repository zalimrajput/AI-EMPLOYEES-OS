-- 0059_seed_default_roles.sql
-- Default human roles (Owner / Admin / Employee) for every organization.
--
-- Human user types are org-scoped (roles + user_roles, see 0041_roles.sql).
-- This migration:
--   1. Seeds the three default roles for every organization (new + existing).
--   2. Binds the organization creator as Owner on org creation when the
--      INSERT happens in an authenticated context (supabase-js frontend flow).
--      Backend-created orgs (FastAPI superuser connection, no auth context)
--      assign the Owner role in application code instead.

CREATE OR REPLACE FUNCTION public.seed_default_roles(p_org_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.roles (organization_id, name, description, permissions)
    VALUES
        (p_org_id, 'Owner',
         'Full control over the workspace, billing, members, and AI workforce.',
         '{"manage_org":true,"manage_members":true,"manage_billing":true,"manage_ai":true,"manage_workflows":true,"use_tools":true}'::jsonb),
        (p_org_id, 'Admin',
         'Manage the AI workforce, workflows, and most workspace settings.',
         '{"manage_ai":true,"manage_workflows":true,"manage_members":false,"manage_billing":false,"use_tools":true}'::jsonb),
        (p_org_id, 'Employee',
         'Use assigned tasks, tools, and AI assistants.',
         '{"use_tools":true,"manage_ai":false,"manage_workflows":false}'::jsonb)
    ON CONFLICT (organization_id, name) DO NOTHING;
END;
$$;

-- On org creation: seed the default roles and, when the insert happens in an
-- authenticated context, bind the creator as Owner. Runs AFTER INSERT so
-- NEW.id exists; the existing trg_set_org_creator (0053) still assigns
-- users.organization_id afterwards (triggers run in alphabetical order).
CREATE OR REPLACE FUNCTION public.handle_new_organization()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_creator_id uuid;
    v_owner_role_id uuid;
BEGIN
    PERFORM public.seed_default_roles(NEW.id);

    v_creator_id := auth.uid();
    IF v_creator_id IS NOT NULL THEN
        SELECT id INTO v_owner_role_id
        FROM public.roles
        WHERE organization_id = NEW.id AND name = 'Owner';
        IF v_owner_role_id IS NOT NULL THEN
            INSERT INTO public.user_roles (user_id, role_id, organization_id)
            VALUES (v_creator_id, v_owner_role_id, NEW.id)
            ON CONFLICT DO NOTHING;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_seed_default_roles ON public.organizations;
CREATE TRIGGER trg_seed_default_roles
    AFTER INSERT ON public.organizations
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_organization();

-- Backfill roles for organizations created before this migration.
DO $$
DECLARE
    o RECORD;
BEGIN
    FOR o IN SELECT id FROM public.organizations LOOP
        PERFORM public.seed_default_roles(o.id);
    END LOOP;
END $$;
