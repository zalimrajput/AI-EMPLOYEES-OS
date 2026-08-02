-- 0060_platform_roles_and_seeds.sql
-- Aligns the DB with the product summary:
--   1) Platform layer: Super Admin (platform_roles), global settings, platform logs.
--   2) Company roles: upgrade the 3-role seed (0059) to the full 11-role model.
--   3) Seed the 12 AI employees per company (with tools + permissions).
--   4) Seed the 14 dashboards per company + role-based dashboard access.
--
-- Total human roles: 1 platform (Super Admin) + 11 company = 12.
-- Note: existing orgs keep their 0059 Owner/Admin/Employee rows (legacy);
--       new roles are added alongside them.

-- =====================================================================
-- 1) PLATFORM LAYER
-- =====================================================================

-- Platform-level role assignment (only role today: Super Admin)
CREATE TABLE IF NOT EXISTS platform_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'Super Admin',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id)
);

-- Platform-wide global settings (key/value)
CREATE TABLE IF NOT EXISTS platform_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key TEXT NOT NULL UNIQUE,
    value JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Platform-level audit / activity logs
CREATE TABLE IF NOT EXISTS platform_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    entity TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Helper: is the current auth user a platform Super Admin?
-- (LANGUAGE sql is parsed at creation time, so it must come AFTER the
--  platform_roles table it references.)
CREATE OR REPLACE FUNCTION public.is_super_admin()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.platform_roles WHERE user_id = auth.uid()
    );
$$;

INSERT INTO public.platform_settings (key, value)
VALUES ('platform_name', '{"name":"AI Employee OS"}'::jsonb)
ON CONFLICT (key) DO NOTHING;

-- Note: the first Super Admin must be bootstrapped manually (service role
-- bypasses RLS), e.g.:
--   INSERT INTO public.platform_roles (user_id, role)
--   SELECT id, 'Super Admin' FROM public.users WHERE email = 'you@company.com';

-- RLS: platform tables are Super-Admin-only (logs allow authenticated insert)
ALTER TABLE public.platform_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.platform_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.platform_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS platform_roles_admin ON public.platform_roles;
CREATE POLICY platform_roles_admin ON public.platform_roles
    FOR ALL USING (public.is_super_admin());

DROP POLICY IF EXISTS platform_settings_admin ON public.platform_settings;
CREATE POLICY platform_settings_admin ON public.platform_settings
    FOR ALL USING (public.is_super_admin());

DROP POLICY IF EXISTS platform_logs_admin ON public.platform_logs;
CREATE POLICY platform_logs_admin ON public.platform_logs
    FOR ALL USING (public.is_super_admin());

DROP POLICY IF EXISTS platform_logs_insert ON public.platform_logs;
CREATE POLICY platform_logs_insert ON public.platform_logs
    FOR INSERT TO authenticated WITH CHECK (true);

GRANT SELECT, INSERT, UPDATE, DELETE ON public.platform_roles, public.platform_settings, public.platform_logs TO authenticated, service_role;

-- =====================================================================
-- 2) COMPANY ROLES — upgrade the 0059 seed to the full 11-role model
-- =====================================================================

CREATE OR REPLACE FUNCTION public.seed_default_roles(p_org_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.roles (organization_id, name, description, permissions)
    VALUES
        (p_org_id, 'Company Admin',
         'Full control over the company workspace, members, billing, and AI workforce.',
         '{"manage_org":true,"manage_members":true,"manage_billing":true,"manage_ai":true,"manage_workflows":true,"use_tools":true}'::jsonb),
        (p_org_id, 'CEO / Executive',
         'Oversee the whole company, view reports and analytics.',
         '{"manage_org":true,"view_all":true,"manage_ai":true,"manage_workflows":true,"use_tools":true}'::jsonb),
        (p_org_id, 'Sales Manager',
         'Manage the sales team, CRM, leads, and quotations.',
         '{"manage_sales":true,"manage_crm":true,"manage_quotations":true,"use_tools":true}'::jsonb),
        (p_org_id, 'Sales Executive',
         'Work leads, deals, and quotations assigned to them.',
         '{"manage_crm":true,"manage_quotations":true,"use_tools":true}'::jsonb),
        (p_org_id, 'HR Manager',
         'Manage employees, hiring, and HR workflows.',
         '{"manage_hr":true,"manage_employees":true,"use_tools":true}'::jsonb),
        (p_org_id, 'Finance Manager',
         'Manage budgets, expenses, and financial reports.',
         '{"manage_finance":true,"manage_budgets":true,"use_tools":true}'::jsonb),
        (p_org_id, 'Accountant',
         'Create invoices, record payments, and manage accounting.',
         '{"manage_invoices":true,"manage_payments":true,"use_tools":true}'::jsonb),
        (p_org_id, 'Customer Support',
         'Respond to customers via email and WhatsApp.',
         '{"manage_support":true,"use_tools":true}'::jsonb),
        (p_org_id, 'Marketing Manager',
         'Manage marketing campaigns and content.',
         '{"manage_marketing":true,"use_tools":true}'::jsonb),
        (p_org_id, 'Operations Manager',
         'Manage tasks, workflows, and daily operations.',
         '{"manage_operations":true,"manage_tasks":true,"manage_workflows":true,"use_tools":true}'::jsonb),
        (p_org_id, 'Employee/User',
         'Use assigned tools, tasks, and AI assistants.',
         '{"use_tools":true}'::jsonb)
    ON CONFLICT (organization_id, name) DO NOTHING;
END;
$$;

-- =====================================================================
-- 3) AI EMPLOYEES — seed the 12 specialized roles per company
-- =====================================================================

-- Dedupe any pre-existing (org, name) pairs so the unique index can't abort
-- the migration on dirty/test data, then create the index.
DELETE FROM public.ai_employees a
USING public.ai_employees b
WHERE a.id > b.id
  AND a.organization_id = b.organization_id
  AND a.name = b.name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_employees_org_name ON public.ai_employees(organization_id, name);

CREATE OR REPLACE FUNCTION public._seed_ai_employee(
    p_org_id UUID, p_name TEXT, p_role TEXT, p_desc TEXT,
    p_model TEXT, p_tools JSONB, p_permissions JSONB
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.ai_employees
        (organization_id, name, role, description, model, tools, permissions, active)
    VALUES
        (p_org_id, p_name, p_role, p_desc, p_model, p_tools, p_permissions, TRUE)
    ON CONFLICT (organization_id, name) DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION public.seed_default_ai_employees(p_org_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    PERFORM public._seed_ai_employee(p_org_id, 'AI Executive Assistant', 'Executive Assistant',
        'Coordinates emails, calendar, tasks, and reporting for executives.',
        'gpt-5', '{"email":true,"calendar":true,"tasks":true,"crm":true,"reporting":true}'::jsonb,
        '{"manage_all":true,"use_tools":true}'::jsonb);
    PERFORM public._seed_ai_employee(p_org_id, 'AI Sales Assistant', 'Sales Assistant',
        'Handles leads, follow-ups, and quotations.',
        'gpt-5', '{"crm":true,"leads":true,"quotations":true,"email":true,"whatsapp":true}'::jsonb,
        '{"manage_sales":true,"use_tools":true}'::jsonb);
    PERFORM public._seed_ai_employee(p_org_id, 'AI Customer Support Agent', 'Customer Support Agent',
        'Resolves customer inquiries via email and WhatsApp.',
        'gpt-5', '{"email":true,"whatsapp":true,"crm":true,"knowledge_base":true}'::jsonb,
        '{"manage_support":true,"use_tools":true}'::jsonb);
    PERFORM public._seed_ai_employee(p_org_id, 'AI HR Assistant', 'HR Assistant',
        'Handles employee records, onboarding, and HR workflows.',
        'gpt-5', '{"hr":true,"employees":true,"tasks":true}'::jsonb,
        '{"manage_hr":true,"use_tools":true}'::jsonb);
    PERFORM public._seed_ai_employee(p_org_id, 'AI Recruiter', 'Recruiter',
        'Screens candidates and supports hiring.',
        'gpt-5', '{"hr":true,"candidates":true,"email":true}'::jsonb,
        '{"manage_hr":true,"use_tools":true}'::jsonb);
    PERFORM public._seed_ai_employee(p_org_id, 'AI Finance Assistant', 'Finance Assistant',
        'Tracks budgets, expenses, and financial reports.',
        'gpt-5', '{"finance":true,"expenses":true,"budgets":true,"reporting":true}'::jsonb,
        '{"manage_finance":true,"use_tools":true}'::jsonb);
    PERFORM public._seed_ai_employee(p_org_id, 'AI Accountant', 'Accountant',
        'Creates invoices, records payments, and prepares accounting.',
        'gpt-5', '{"invoices":true,"payments":true,"finance":true,"email":true}'::jsonb,
        '{"manage_finance":true,"manage_invoices":true,"use_tools":true}'::jsonb);
    PERFORM public._seed_ai_employee(p_org_id, 'AI Marketing Assistant', 'Marketing Assistant',
        'Plans campaigns, segments audiences, and drafts content.',
        'gpt-5', '{"marketing":true,"email_campaigns":true,"content":true}'::jsonb,
        '{"manage_marketing":true,"use_tools":true}'::jsonb);
    PERFORM public._seed_ai_employee(p_org_id, 'AI Content Writer', 'Content Writer',
        'Drafts and edits marketing and company content.',
        'gpt-5', '{"content":true,"documents":true,"knowledge_base":true}'::jsonb,
        '{"use_tools":true}'::jsonb);
    PERFORM public._seed_ai_employee(p_org_id, 'AI Legal Assistant', 'Legal Assistant',
        'Analyzes contracts and policy documents.',
        'gpt-5', '{"documents":true,"knowledge_base":true,"contracts":true}'::jsonb,
        '{"use_tools":true}'::jsonb);
    PERFORM public._seed_ai_employee(p_org_id, 'AI Inventory Manager', 'Inventory Manager',
        'Tracks stock levels, reorders, and inventory movements.',
        'gpt-5', '{"inventory":true,"warehouses":true,"products":true,"reporting":true}'::jsonb,
        '{"manage_inventory":true,"use_tools":true}'::jsonb);
    PERFORM public._seed_ai_employee(p_org_id, 'AI Procurement Assistant', 'Procurement Assistant',
        'Manages suppliers and purchase orders.',
        'gpt-5', '{"suppliers":true,"purchase_orders":true,"inventory":true,"email":true}'::jsonb,
        '{"manage_inventory":true,"use_tools":true}'::jsonb);
END;
$$;

-- =====================================================================
-- 4) DASHBOARDS — seed the 14 dashboards + role-based access
-- =====================================================================

-- Dedupe pre-existing (org, name) pairs before creating the unique index.
DELETE FROM public.dashboards a
USING public.dashboards b
WHERE a.id > b.id
  AND a.organization_id = b.organization_id
  AND a.name = b.name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_dashboards_org_name ON public.dashboards(organization_id, name);

-- dashboard_role_access maps dashboards to the roles that may see them
CREATE TABLE IF NOT EXISTS dashboard_role_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    role_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (dashboard_id, role_name)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_role_access_org ON dashboard_role_access(organization_id);

ALTER TABLE public.dashboard_role_access ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS dashboard_role_access_tenant ON public.dashboard_role_access;
CREATE POLICY dashboard_role_access_tenant ON public.dashboard_role_access
    FOR ALL USING (organization_id = public.current_org_id());

GRANT SELECT, INSERT, UPDATE, DELETE ON public.dashboard_role_access TO authenticated, service_role;

CREATE OR REPLACE FUNCTION public._seed_dashboard(
    p_org_id UUID, p_name TEXT, p_desc TEXT, p_roles TEXT[]
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_dashboard_id uuid;
BEGIN
    INSERT INTO public.dashboards (organization_id, name, description, layout)
    VALUES (p_org_id, p_name, p_desc, '{"widgets":[]}'::jsonb)
    ON CONFLICT (organization_id, name) DO NOTHING;

    SELECT id INTO v_dashboard_id
    FROM public.dashboards
    WHERE organization_id = p_org_id AND name = p_name;

    IF v_dashboard_id IS NOT NULL THEN
        INSERT INTO public.dashboard_role_access (organization_id, dashboard_id, role_name)
        SELECT p_org_id, v_dashboard_id, unnest(p_roles)
        ON CONFLICT DO NOTHING;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION public.seed_default_dashboards(p_org_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    PERFORM public._seed_dashboard(p_org_id, 'Super Admin Dashboard',
        'Platform-wide administration and company oversight.', ARRAY['Super Admin']);
    PERFORM public._seed_dashboard(p_org_id, 'Company Admin Dashboard',
        'Company-wide overview and member management.', ARRAY['Company Admin']);
    PERFORM public._seed_dashboard(p_org_id, 'CEO / Executive Dashboard',
        'Executive KPIs, revenue, and high-level analytics.', ARRAY['CEO / Executive']);
    PERFORM public._seed_dashboard(p_org_id, 'Sales Dashboard',
        'Sales pipeline, leads, and quotation performance.', ARRAY['Sales Manager', 'Sales Executive']);
    PERFORM public._seed_dashboard(p_org_id, 'CRM Dashboard',
        'Customers, leads, and relationship insights.', ARRAY['Company Admin', 'Sales Manager', 'Sales Executive']);
    PERFORM public._seed_dashboard(p_org_id, 'HR Dashboard',
        'Employees, attendance, and hiring overview.', ARRAY['HR Manager']);
    PERFORM public._seed_dashboard(p_org_id, 'Finance Dashboard',
        'Revenue, expenses, budgets, and cash flow.', ARRAY['Finance Manager', 'Accountant']);
    PERFORM public._seed_dashboard(p_org_id, 'Customer Support Dashboard',
        'Support tickets, email, and WhatsApp activity.', ARRAY['Customer Support']);
    PERFORM public._seed_dashboard(p_org_id, 'Marketing Dashboard',
        'Campaigns, content, and audience performance.', ARRAY['Marketing Manager']);
    PERFORM public._seed_dashboard(p_org_id, 'Operations Dashboard',
        'Tasks, workflows, and operational efficiency.', ARRAY['Operations Manager']);
    PERFORM public._seed_dashboard(p_org_id, 'Employee Dashboard',
        'Personal tasks, deadlines, and AI assistant access.', ARRAY['Employee/User']);
    PERFORM public._seed_dashboard(p_org_id, 'AI Employees Dashboard',
        'Manage the AI workforce, tools, and usage.', ARRAY['Company Admin', 'CEO / Executive']);
    PERFORM public._seed_dashboard(p_org_id, 'Reports & Analytics Dashboard',
        'Reports and analytics for managers and above.', ARRAY['Company Admin', 'CEO / Executive',
            'Sales Manager', 'HR Manager', 'Finance Manager', 'Marketing Manager', 'Operations Manager']);
    PERFORM public._seed_dashboard(p_org_id, 'Settings & Integrations Dashboard',
        'Company settings and connected applications.', ARRAY['Company Admin', 'CEO / Executive']);
END;
$$;

-- =====================================================================
-- 5) ORG CREATION TRIGGER — seed roles, AI employees, dashboards, and
--    bind the creator as Company Admin (frontend flow, auth context).
-- =====================================================================

CREATE OR REPLACE FUNCTION public.handle_new_organization()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_creator_id uuid;
    v_creator_role_id uuid;
BEGIN
    PERFORM public.seed_default_roles(NEW.id);
    PERFORM public.seed_default_ai_employees(NEW.id);
    PERFORM public.seed_default_dashboards(NEW.id);

    v_creator_id := auth.uid();
    IF v_creator_id IS NOT NULL THEN
        SELECT id INTO v_creator_role_id
        FROM public.roles
        WHERE organization_id = NEW.id AND name = 'Company Admin';
        IF v_creator_role_id IS NOT NULL THEN
            INSERT INTO public.user_roles (user_id, role_id, organization_id)
            VALUES (v_creator_id, v_creator_role_id, NEW.id)
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

-- =====================================================================
-- 6) BACKFILL — apply the full seeds to organizations created before 0060
-- =====================================================================

DO $$
DECLARE
    o RECORD;
BEGIN
    FOR o IN SELECT id FROM public.organizations LOOP
        PERFORM public.seed_default_roles(o.id);
        PERFORM public.seed_default_ai_employees(o.id);
        PERFORM public.seed_default_dashboards(o.id);
    END LOOP;
END $$;

-- Legacy creators (0059) held the 'Owner' role; unify them onto the new
-- Company Admin role so the 12-role model is consistent across all orgs.
INSERT INTO public.user_roles (user_id, role_id, organization_id)
SELECT ur.user_id, ca.id, ur.organization_id
FROM public.user_roles ur
JOIN public.roles o ON o.id = ur.role_id AND o.name = 'Owner'
JOIN public.roles ca
    ON ca.organization_id = ur.organization_id
   AND ca.name = 'Company Admin'
ON CONFLICT DO NOTHING;
