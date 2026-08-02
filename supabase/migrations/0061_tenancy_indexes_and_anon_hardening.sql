-- 0061_tenancy_indexes_and_anon_hardening.sql
-- Security hardening identified by the live tenant-security audit
-- (backend/scripts/audit_tenant_security.py + audit_policies_detail.py):
--
--   1) 40 FK / tenancy columns had NO index. Every RLS query filters on
--      `organization_id = current_org_id()`, so an index on that column is
--      what keeps multi-tenant lookups fast and prevents cross-tenant
--      sequential scans (and potential row-lock escalation on UPDATE/DELETE).
--   2) `anon` held blanket SELECT (and TRIGGER/TRUNCATE/REFERENCES) grants on
--      ALL 75 tables. RLS already blocks anon (auth.uid() is NULL), but a
--      future table added without RLS, or a stray permissive policy, would
--      silently expose it. Defense-in-depth: anon keeps SELECT only on
--      `plans` (the public catalog with a `FOR SELECT USING (true)` policy).

-- =====================================================================
-- 1) INDEXES on FK / tenancy columns missing them
--    (generated live: backend/scripts/gen_fk_indexes.py)
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_activities_user_id ON public.activities(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_memories_employee_id ON public.ai_memories(employee_id);
CREATE INDEX IF NOT EXISTS idx_ai_memories_organization_id ON public.ai_memories(organization_id);
CREATE INDEX IF NOT EXISTS idx_ai_messages_organization_id ON public.ai_messages(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_created_by ON public.api_keys(created_by);
CREATE INDEX IF NOT EXISTS idx_api_requests_api_key_id ON public.api_requests(api_key_id);
CREATE INDEX IF NOT EXISTS idx_attendance_employee_id ON public.attendance(employee_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_dashboards_created_by ON public.dashboards(created_by);
CREATE INDEX IF NOT EXISTS idx_departments_organization_id ON public.departments(organization_id);
CREATE INDEX IF NOT EXISTS idx_documents_organization_id ON public.documents(organization_id);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON public.documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_employees_user_id ON public.employees(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_approved_by ON public.expenses(approved_by);
CREATE INDEX IF NOT EXISTS idx_expenses_category_id ON public.expenses(category_id);
CREATE INDEX IF NOT EXISTS idx_expenses_submitted_by ON public.expenses(submitted_by);
CREATE INDEX IF NOT EXISTS idx_file_access_permissions_organization_id ON public.file_access_permissions(organization_id);
CREATE INDEX IF NOT EXISTS idx_file_access_permissions_user_id ON public.file_access_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_financial_reports_generated_by ON public.financial_reports(generated_by);
CREATE INDEX IF NOT EXISTS idx_integrations_organization_id ON public.integrations(organization_id);
CREATE INDEX IF NOT EXISTS idx_invoice_items_product_id ON public.invoice_items(product_id);
CREATE INDEX IF NOT EXISTS idx_leads_converted_customer_id ON public.leads(converted_customer_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_approved_by ON public.leave_requests(approved_by);
CREATE INDEX IF NOT EXISTS idx_leave_requests_employee_id ON public.leave_requests(employee_id);
CREATE INDEX IF NOT EXISTS idx_marketing_campaigns_created_by ON public.marketing_campaigns(created_by);
CREATE INDEX IF NOT EXISTS idx_marketing_content_organization_id ON public.marketing_content(organization_id);
CREATE INDEX IF NOT EXISTS idx_mfa_settings_organization_id ON public.mfa_settings(organization_id);
CREATE INDEX IF NOT EXISTS idx_platform_logs_user_id ON public.platform_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_quotation_items_product_id ON public.quotation_items(product_id);
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON public.reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_generated_by ON public.reports(generated_by);
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON public.security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_organization_id ON public.stock_movements(organization_id);
CREATE INDEX IF NOT EXISTS idx_storage_files_uploaded_by ON public.storage_files(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_tasks_organization_id ON public.tasks(organization_id);
CREATE INDEX IF NOT EXISTS idx_usage_records_ai_employee_id ON public.usage_records(ai_employee_id);
CREATE INDEX IF NOT EXISTS idx_usage_records_user_id ON public.usage_records(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_organization_id ON public.user_sessions(organization_id);
CREATE INDEX IF NOT EXISTS idx_warehouses_manager_id ON public.warehouses(manager_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_customer_id ON public.whatsapp_contacts(customer_id);

-- =====================================================================
-- 2) ANON HARDENING — remove blanket grants; keep only the public catalog
-- =====================================================================
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;

-- `plans` is the public pricing catalog (`plans_read` allows any role).
GRANT SELECT ON public.plans TO anon;

-- Future tables must NOT re-grant anon access by default.
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT ON TABLES FROM anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon;
