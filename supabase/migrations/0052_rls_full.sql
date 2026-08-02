-- 0052_rls_full.sql
-- Full multi-tenant security: RLS on EVERY table with tenant isolation.
-- Uses a SECURITY DEFINER helper to avoid recursive RLS lookups.

-- Helper: organization_id of the currently authenticated user (NULL if none)
CREATE OR REPLACE FUNCTION public.current_org_id()
RETURNS UUID
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT organization_id
    FROM public.users
    WHERE id = auth.uid()
$$;

-- Drop legacy policies from migration 0033. They are self-referential on
-- public.users (recursive RLS) and are fully replaced by the policies below.
DROP POLICY IF EXISTS organizations_isolation ON organizations;
DROP POLICY IF EXISTS users_isolation ON users;
DROP POLICY IF EXISTS departments_isolation ON departments;
DROP POLICY IF EXISTS ai_employee_isolation ON ai_employees;
DROP POLICY IF EXISTS customers_isolation ON customers;
DROP POLICY IF EXISTS tasks_isolation ON tasks;
DROP POLICY IF EXISTS documents_isolation ON documents;
DROP POLICY IF EXISTS storage_files_isolation ON storage_files;

-- Tables with organization_id get the standard tenant policy.
-- (organizations itself is keyed by id, users also has a self-access policy.)
DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'users', 'departments', 'ai_employees', 'ai_memories', 'integrations',
        'customers', 'deals', 'products', 'quotations', 'invoices', 'payments',
        'email_threads', 'emails', 'whatsapp_contacts', 'whatsapp_messages',
        'tasks', 'meetings', 'documents', 'knowledge_articles', 'workflows',
        'notifications', 'audit_logs', 'employees', 'attendance',
        'leave_requests', 'job_candidates', 'expense_categories', 'expenses',
        'budgets', 'financial_reports', 'warehouses', 'suppliers',
        'inventory_items', 'stock_movements', 'purchase_orders',
        'marketing_campaigns', 'audience_segments', 'marketing_content',
        'email_campaigns', 'dashboards', 'reports', 'analytics_events',
        'business_metrics', 'subscriptions', 'billing_transactions',
        'usage_records', 'storage_usage', 'api_usage', 'api_keys', 'webhooks',
        'api_requests', 'user_sessions', 'mfa_settings', 'sso_connections',
        'security_events', 'storage_files', 'storage_quotas',
        'file_access_permissions', 'ai_conversations', 'ai_messages',
        'organization_settings', 'roles', 'user_roles', 'leads', 'pipelines',
        'reminders', 'quotation_items', 'invoice_items', 'activities'
    ] LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', t);
        EXECUTE format(
            'DROP POLICY IF EXISTS %I ON %I;',
            t || '_tenant_isolation', t
        );
        EXECUTE format(
            'CREATE POLICY %I ON %I FOR ALL USING (organization_id = public.current_org_id());',
            t || '_tenant_isolation', t
        );
    END LOOP;
END $$;

-- organizations: keyed by id
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS organizations_tenant_isolation ON organizations;
CREATE POLICY organizations_tenant_isolation ON organizations
    FOR ALL USING (id = public.current_org_id());

-- users: tenant isolation (org member) OR self access
DROP POLICY IF EXISTS users_tenant_isolation ON users;
CREATE POLICY users_tenant_isolation ON users
    FOR ALL USING (organization_id = public.current_org_id());
-- (users_self_access for SELECT was created in 0040)

-- plans: global catalog readable by authenticated users, no org scoping
ALTER TABLE plans ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS plans_read ON plans;
CREATE POLICY plans_read ON plans
    FOR SELECT USING (true);
