-- 0064_super_admin_rls_ai_integrations.sql
-- Extends cross-tenant visibility to the Super Admin for the remaining
-- tenant-scoped tables the platform dashboard reads:
--   * ai_employees  (the "AI models" tile counts every deployed agent)
--   * integrations  (the "Integrations" tile counts connected apps)
--
-- Mirrors the 0062 pattern: `organization_id = current_org_id() OR is_super_admin()`.
-- is_super_admin() is SECURITY DEFINER (0060) — no RLS recursion.

DROP POLICY IF EXISTS ai_employees_tenant_isolation ON ai_employees;
CREATE POLICY ai_employees_tenant_isolation ON ai_employees
    FOR ALL USING (
        organization_id = public.current_org_id()
        OR public.is_super_admin()
    );

DROP POLICY IF EXISTS integrations_tenant_isolation ON integrations;
CREATE POLICY integrations_tenant_isolation ON integrations
    FOR ALL USING (
        organization_id = public.current_org_id()
        OR public.is_super_admin()
    );
