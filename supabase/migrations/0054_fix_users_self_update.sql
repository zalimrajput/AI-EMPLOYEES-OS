-- 0054_fix_users_self_update.sql
-- Security fix: users_self_update (0053) let a user change their own
-- organization_id, which would allow self-joining another tenant and
-- bypassing RLS on every table. Constrain organization_id in WITH CHECK.

DROP POLICY IF EXISTS users_self_update ON users;
CREATE POLICY users_self_update ON users
    FOR UPDATE
    USING (id = auth.uid())
    WITH CHECK (
        id = auth.uid()
        AND organization_id IS NOT DISTINCT FROM public.current_org_id()
    );

-- Also harden users_tenant_isolation so org members cannot rewrite an
-- org-mate's organization_id (reassignments go through service_role/backend).
DROP POLICY IF EXISTS users_tenant_isolation ON users;
CREATE POLICY users_tenant_isolation ON users
    FOR ALL
    USING (organization_id = public.current_org_id())
    WITH CHECK (organization_id = public.current_org_id());
