-- 0062_org_modules_and_org_admin.sql
-- Platform-module control for the AI Employee OS SaaS model:
--   * Super Admin: sees ALL organizations (cross-tenant read/manage) and
--     enables/disables modules per organization (enabled_by_super_admin).
--   * Org Admin (Company Admin): self-service management of users, roles, and
--     which enabled modules their organization actually uses
--     (enabled_by_org_admin). A module is visible only when BOTH flags are on.
--   * Regular users: only see dashboards/nav for modules enabled in their org
--     and permitted by their role (existing dashboard_role_access).

-- =====================================================================
-- 1) MODULE CATALOG (global, seeded; not per-org)
-- =====================================================================
CREATE TABLE IF NOT EXISTS modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT DEFAULT 'Box',
    group_name TEXT DEFAULT 'operations',
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE modules ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS modules_read ON modules;
CREATE POLICY modules_read ON modules
    FOR SELECT USING (true);

-- =====================================================================
-- 2) PER-ORG MODULE SETTINGS
-- =====================================================================
CREATE TABLE IF NOT EXISTS org_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL
        REFERENCES organizations(id) ON DELETE CASCADE,
    module_key TEXT NOT NULL,
    enabled_by_super_admin BOOLEAN DEFAULT TRUE,
    enabled_by_org_admin BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (organization_id, module_key)
);

CREATE INDEX IF NOT EXISTS idx_org_modules_org ON org_modules(organization_id);

ALTER TABLE org_modules ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS org_modules_tenant ON org_modules;
CREATE POLICY org_modules_tenant ON org_modules
    FOR ALL USING (organization_id = public.current_org_id());
DROP POLICY IF EXISTS org_modules_super_admin ON org_modules;
CREATE POLICY org_modules_super_admin ON org_modules
    FOR ALL USING (public.is_super_admin());

GRANT SELECT, INSERT, UPDATE, DELETE ON public.org_modules TO authenticated, service_role;
GRANT SELECT ON public.modules TO authenticated, service_role;

-- =====================================================================
-- 3) ORG PLAN / STATUS COLUMNS (super admin platform view)
-- =====================================================================
ALTER TABLE organizations
    ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'Trial',
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS max_users INT,
    ADD COLUMN IF NOT EXISTS storage_limit_gb INT,
    ADD COLUMN IF NOT EXISTS ai_requests_limit INT;

-- Backfill plan limits from the active subscription, if any.
UPDATE organizations o
SET plan = p.name,
    max_users = p.max_users,
    storage_limit_gb = p.storage_limit_gb,
    ai_requests_limit = p.ai_requests_limit
FROM subscriptions s
JOIN plans p ON p.id = s.plan_id
WHERE s.organization_id = o.id
  AND s.status = 'active'
  AND (o.plan IS NULL OR o.plan = 'Trial');

-- =====================================================================
-- 4) SUPER ADMIN CROSS-TENANT VISIBILITY
--    is_super_admin() is SECURITY DEFINER (0060) — no RLS recursion.
-- =====================================================================
DROP POLICY IF EXISTS organizations_tenant_isolation ON organizations;
CREATE POLICY organizations_tenant_isolation ON organizations
    FOR ALL USING (
        id = public.current_org_id()
        OR created_by = auth.uid()
        OR public.is_super_admin()
    );

DROP POLICY IF EXISTS users_tenant_isolation ON users;
CREATE POLICY users_tenant_isolation ON users
    FOR ALL USING (
        organization_id = public.current_org_id()
        OR public.is_super_admin()
    );

DROP POLICY IF EXISTS dashboards_tenant_isolation ON dashboards;
CREATE POLICY dashboards_tenant_isolation ON dashboards
    FOR ALL USING (
        organization_id = public.current_org_id()
        OR public.is_super_admin()
    );

DROP POLICY IF EXISTS dashboard_role_access_tenant ON dashboard_role_access;
CREATE POLICY dashboard_role_access_tenant ON dashboard_role_access
    FOR ALL USING (
        organization_id = public.current_org_id()
        OR public.is_super_admin()
    );

-- =====================================================================
-- 5) SEED MODULES + PER-ORG ROWS (backfill + trigger for new orgs)
-- =====================================================================
INSERT INTO modules (key, name, description, icon, group_name, sort_order) VALUES
('overview', 'Overview', 'Company-wide overview and quick stats.', 'LayoutDashboard', 'core', 0),
('crm', 'CRM', 'Customers, leads, and relationship insights.', 'Users', 'sales', 1),
('sales', 'Sales & Quotations', 'Sales pipeline, leads, and quotations.', 'TrendingUp', 'sales', 2),
('finance', 'Finance & Invoices', 'Invoices, payments, budgets, and cash flow.', 'Wallet', 'finance', 3),
('hr', 'HR & People', 'Employees, attendance, and hiring.', 'UserCog', 'people', 4),
('marketing', 'Marketing', 'Campaigns, content, and audience.', 'Megaphone', 'growth', 5),
('operations', 'Operations', 'Tasks, workflows, and daily operations.', 'Workflow', 'operations', 6),
('support', 'Customer Support', 'Email, WhatsApp, and tickets.', 'Headset', 'customer', 7),
('tasks', 'Tasks', 'Task creation, assignment, and progress.', 'Kanban', 'operations', 8),
('workflows', 'Workflows', 'Workflow automation.', 'Workflow', 'operations', 9),
('meetings', 'Meetings', 'Meeting summaries and action items.', 'Calendar', 'productivity', 10),
('documents', 'Documents', 'Document intelligence and knowledge base.', 'FileText', 'productivity', 11),
('reports', 'Reports & Analytics', 'Reporting and analytics dashboards.', 'BarChart3', 'operations', 12),
('ai_employees', 'AI Employees', 'The AI workforce.', 'Bot', 'core', 13),
('billing', 'Billing', 'Subscriptions, usage, and payments.', 'CreditCard', 'admin', 14),
('settings', 'Settings', 'Organization settings and integrations.', 'Settings', 'admin', 15)
ON CONFLICT (key) DO NOTHING;

-- Seed all modules (both flags ON) for a given organization.
CREATE OR REPLACE FUNCTION public.seed_org_modules(p_org_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO org_modules (organization_id, module_key)
    SELECT p_org_id, key FROM modules
    ON CONFLICT (organization_id, module_key) DO NOTHING;
END;
$$;

-- Trigger: new organizations get the full module set automatically.
CREATE OR REPLACE FUNCTION public.handle_new_org_modules()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    PERFORM public.seed_org_modules(NEW.id);
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_seed_org_modules ON organizations;
CREATE TRIGGER trg_seed_org_modules
    AFTER INSERT ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_org_modules();

-- Backfill: organizations created before this migration.
DO $$
DECLARE o RECORD;
BEGIN
    FOR o IN SELECT id FROM public.organizations LOOP
        PERFORM public.seed_org_modules(o.id);
    END LOOP;
END $$;
