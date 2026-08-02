-- 0039_indexes.sql
-- Add missing indexes on FK columns and org_id columns for query performance.

CREATE INDEX IF NOT EXISTS idx_deals_org ON deals(organization_id);
CREATE INDEX IF NOT EXISTS idx_deals_customer ON deals(customer_id);

CREATE INDEX IF NOT EXISTS idx_products_org ON products(organization_id);

CREATE INDEX IF NOT EXISTS idx_quotations_org ON quotations(organization_id);
CREATE INDEX IF NOT EXISTS idx_quotations_customer ON quotations(customer_id);

CREATE INDEX IF NOT EXISTS idx_invoices_org ON invoices(organization_id);
CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);

CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payments_org ON payments(organization_id);

CREATE INDEX IF NOT EXISTS idx_email_threads_org ON email_threads(organization_id);
CREATE INDEX IF NOT EXISTS idx_email_threads_customer ON email_threads(customer_id);
CREATE INDEX IF NOT EXISTS idx_email_threads_priority ON email_threads(ai_priority);

CREATE INDEX IF NOT EXISTS idx_emails_thread ON emails(thread_id);
CREATE INDEX IF NOT EXISTS idx_emails_org ON emails(organization_id);

CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_org ON whatsapp_contacts(organization_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_contact ON whatsapp_messages(contact_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_org ON whatsapp_messages(organization_id);

CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

CREATE INDEX IF NOT EXISTS idx_meetings_org ON meetings(organization_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_articles_org ON knowledge_articles(organization_id);

CREATE INDEX IF NOT EXISTS idx_workflows_org ON workflows(organization_id);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_org ON notifications(organization_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_org ON audit_logs(organization_id);

CREATE INDEX IF NOT EXISTS idx_employees_org ON employees(organization_id);
CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_attendance_org ON attendance(organization_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_org ON leave_requests(organization_id);

CREATE INDEX IF NOT EXISTS idx_job_candidates_org ON job_candidates(organization_id);
CREATE INDEX IF NOT EXISTS idx_expense_categories_org ON expense_categories(organization_id);
CREATE INDEX IF NOT EXISTS idx_budgets_org ON budgets(organization_id);
CREATE INDEX IF NOT EXISTS idx_storage_usage_org ON storage_usage(organization_id);

CREATE INDEX IF NOT EXISTS idx_warehouses_org ON warehouses(organization_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_org ON suppliers(organization_id);
CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory_items(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_warehouse ON inventory_items(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_org ON purchase_orders(organization_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id);

CREATE INDEX IF NOT EXISTS idx_audience_segments_org ON audience_segments(organization_id);
CREATE INDEX IF NOT EXISTS idx_email_campaigns_org ON email_campaigns(organization_id);
CREATE INDEX IF NOT EXISTS idx_email_campaigns_campaign ON email_campaigns(campaign_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_plan ON subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_subscription ON billing_transactions(subscription_id);
CREATE INDEX IF NOT EXISTS idx_mfa_settings_user ON mfa_settings(user_id);
