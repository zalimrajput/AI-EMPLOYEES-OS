-- 0063_modules_widgets_dashboards.sql
-- Expands the module system to the full product spec (18 business modules),
-- maps every module to the dashboard it powers, and adds a global widgets
-- catalog so every dashboard can render its module's widgets.
--
-- Module lifecycle (as built in 0062):
--   Super Admin -> enabled_by_super_admin  (platform control)
--   Org Admin   -> enabled_by_org_admin    (workspace choice)
-- A dashboard/widget area is visible only when BOTH flags are on.

-- =====================================================================
-- 1) MODULES CATALOG — expand to the spec + dashboard mapping
-- =====================================================================
ALTER TABLE modules ADD COLUMN IF NOT EXISTS dashboard TEXT;

-- Upsert the full catalog. Existing keys keep their rows; new spec modules
-- are added; every row gets a dashboard mapping (names match 0060 seeds).
INSERT INTO modules (key, name, description, icon, group_name, sort_order, dashboard)
VALUES
  ('overview',     'Overview',                'Company-wide overview and quick stats.',            'LayoutDashboard', 'core',    0,  'Company Admin Dashboard'),
  ('organization', 'Organization Management', 'Organizations, company settings, subscription, and storage usage.', 'Building2', 'admin', 1, 'Company Admin Dashboard'),
  ('users_roles',  'User & Role Management',  'Users, departments, roles, and permissions.',       'Users',           'admin',   2,  'Company Admin Dashboard'),
  ('security',     'Authentication & Security','Login history, MFA status, active sessions, and security alerts.', 'ShieldCheck', 'admin', 3, 'Company Admin Dashboard'),
  ('executive',    'AI Executive Assistant',  'AI tasks completed, pending approvals, insights, and business forecast.', 'Sparkles', 'core', 4, 'CEO / Executive Dashboard'),
  ('ai_employees', 'AI Employees',            'Active AI agents, AI requests, success rate, tool usage, and memory.', 'Bot', 'core', 5, 'AI Employees Dashboard'),
  ('email',        'Email Management',        'Email queue, drafts, follow-ups, and email analytics.', 'Mail', 'customer', 6, 'Customer Support Dashboard'),
  ('whatsapp',     'WhatsApp Communication',  'WhatsApp chats, response time, satisfaction, and open conversations.', 'MessageCircle', 'customer', 7, 'Customer Support Dashboard'),
  ('crm',          'CRM',                     'Customers, new leads, sales pipeline, customer timeline, and AI summaries.', 'Users', 'sales', 8, 'CRM Dashboard'),
  ('sales',        'Quotation Management',    'Quotations, pending and approved quotations, and revenue.', 'TrendingUp', 'sales', 9, 'Sales Dashboard'),
  ('finance',      'Invoice & Payments',      'Invoices, payments, outstanding invoices, cash flow, and profit.', 'Wallet', 'finance', 10, 'Finance Dashboard'),
  ('meetings',     'Meetings & Calendar',     'Today''s meetings, calendar, AI summaries, and action items.', 'Calendar', 'productivity', 11, 'Operations Dashboard'),
  ('documents',    'Document Intelligence',   'OCR queue, recent documents, knowledge base, and AI search.', 'FileText', 'productivity', 12, 'Operations Dashboard'),
  ('tasks',        'Task Management',         'Assigned tasks, due tasks, completed tasks, and AI reminders.', 'Kanban', 'operations', 13, 'Employee Dashboard'),
  ('workflows',    'Workflow Automation',     'Running workflows, failed workflows, and automation history.', 'Workflow', 'operations', 14, 'Operations Dashboard'),
  ('reports',      'Reporting & Analytics',   'Sales reports, revenue reports, customer analytics, employee productivity, and forecasting.', 'BarChart3', 'operations', 15, 'Reports & Analytics Dashboard'),
  ('integrations', 'Integrations',            'Gmail, Outlook, WhatsApp, Google Calendar, Microsoft 365, and API status.', 'Plug', 'admin', 16, 'Company Admin Dashboard'),
  ('notifications','Notifications',           'Recent notifications, email alerts, WhatsApp alerts, and task reminders.', 'Bell', 'core', 17, NULL),
  ('audit',        'Audit Logs',              'User activity, AI activity, login history, and audit logs.', 'ScrollText', 'admin', 18, 'Company Admin Dashboard'),
  ('hr',           'HR & People',             'Employees, attendance, and hiring.',                  'UserCog', 'people', 19, 'HR Dashboard'),
  ('marketing',    'Marketing',               'Campaigns, content, and audience.',                   'Megaphone', 'growth', 20, 'Marketing Dashboard'),
  ('operations',   'Operations',              'Tasks, workflows, and daily operations.',             'Workflow', 'operations', 21, 'Operations Dashboard'),
  ('support',      'Customer Support',        'Email, WhatsApp, and tickets.',                       'Headset', 'customer', 22, 'Customer Support Dashboard'),
  ('billing',      'Billing',                 'Subscriptions, usage, and payments.',                 'CreditCard', 'admin', 23, 'Company Admin Dashboard'),
  ('settings',     'Settings',                'Organization settings and integrations.',             'Settings', 'admin', 24, 'Settings & Integrations Dashboard')
ON CONFLICT (key) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  icon = EXCLUDED.icon,
  group_name = EXCLUDED.group_name,
  sort_order = EXCLUDED.sort_order,
  dashboard = EXCLUDED.dashboard;

-- =====================================================================
-- 2) WIDGETS CATALOG (global, read-only for orgs)
-- =====================================================================
CREATE TABLE IF NOT EXISTS widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_key TEXT NOT NULL REFERENCES modules(key) ON DELETE CASCADE,
    widget_key TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT DEFAULT 'Box',
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (module_key, widget_key)
);

CREATE INDEX IF NOT EXISTS idx_widgets_module ON widgets(module_key);

ALTER TABLE widgets ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS widgets_read ON widgets;
CREATE POLICY widgets_read ON widgets FOR SELECT USING (true);

GRANT SELECT ON public.widgets TO authenticated, service_role;

-- Seed the spec's widgets per module.
INSERT INTO widgets (module_key, widget_key, name, description, icon, sort_order) VALUES
  -- Organization Management
  ('organization', 'orgs', 'Organizations', 'Companies under this account', 'Building2', 0),
  ('organization', 'company_settings', 'Company Settings', 'Profile, branding, and defaults', 'Settings', 1),
  ('organization', 'subscription', 'Subscription', 'Plan, renewal, and status', 'CreditCard', 2),
  ('organization', 'storage', 'Storage Usage', 'Used vs allocated storage', 'HardDrive', 3),
  -- User & Role Management
  ('users_roles', 'users', 'Users', 'Team members and invitations', 'Users', 0),
  ('users_roles', 'departments', 'Departments', 'Structure and membership', 'Building2', 1),
  ('users_roles', 'roles', 'Roles', 'Role definitions and permissions', 'ShieldCheck', 2),
  ('users_roles', 'permissions', 'Permissions', 'Granular access matrix', 'KeyRound', 3),
  -- Authentication & Security
  ('security', 'login_history', 'Login History', 'Recent sign-ins', 'LogIn', 0),
  ('security', 'mfa_status', 'MFA Status', 'Two-factor enrollment', 'ShieldCheck', 1),
  ('security', 'active_sessions', 'Active Sessions', 'Live sessions and devices', 'MonitorSmartphone', 2),
  ('security', 'security_alerts', 'Security Alerts', 'Suspicious activity', 'AlertTriangle', 3),
  -- AI Executive Assistant
  ('executive', 'ai_tasks_done', 'AI Tasks Completed', 'Work finished by AI', 'CheckCircle2', 0),
  ('executive', 'pending_approvals', 'Pending Approvals', 'Items awaiting approval', 'Clock3', 1),
  ('executive', 'ai_insights', 'AI Insights', 'Automated business insights', 'Lightbulb', 2),
  ('executive', 'forecast', 'Business Forecast', 'Projected performance', 'TrendingUp', 3),
  -- AI Employees
  ('ai_employees', 'active_agents', 'Active AI Agents', 'Employees currently online', 'Bot', 0),
  ('ai_employees', 'ai_requests', 'AI Requests', 'Requests handled this period', 'Activity', 1),
  ('ai_employees', 'success_rate', 'Success Rate', 'Completed vs attempted', 'Target', 2),
  ('ai_employees', 'tool_usage', 'Tool Usage', 'Tools called by agents', 'Wrench', 3),
  ('ai_employees', 'memory_usage', 'Memory Usage', 'Context and memory load', 'Brain', 4),
  -- Email Management
  ('email', 'email_queue', 'Email Queue', 'Outbound messages pending', 'Mail', 0),
  ('email', 'drafts', 'Drafts', 'Unsent drafts', 'FileText', 1),
  ('email', 'followups', 'Follow-ups', 'Scheduled follow-ups', 'Repeat', 2),
  ('email', 'email_analytics', 'Email Analytics', 'Open, reply, and bounce rates', 'BarChart3', 3),
  -- WhatsApp Communication
  ('whatsapp', 'whatsapp_chats', 'WhatsApp Chats', 'Conversations and threads', 'MessageCircle', 0),
  ('whatsapp', 'response_time', 'Response Time', 'Avg reply latency', 'Timer', 1),
  ('whatsapp', 'satisfaction', 'Customer Satisfaction', 'CSAT scores', 'Smile', 2),
  ('whatsapp', 'open_conversations', 'Open Conversations', 'Chats needing attention', 'MessageSquare', 3),
  -- CRM
  ('crm', 'customers', 'Customers', 'Total customers and value', 'Users', 0),
  ('crm', 'new_leads', 'New Leads', 'Leads captured this period', 'UserPlus', 1),
  ('crm', 'pipeline', 'Sales Pipeline', 'Deals by stage', 'TrendingUp', 2),
  ('crm', 'customer_timeline', 'Customer Timeline', 'Interaction history', 'Clock', 3),
  ('crm', 'ai_customer_summary', 'AI Customer Summary', 'AI-generated relationship insights', 'Sparkles', 4),
  -- Quotation Management
  ('sales', 'quotations', 'Quotations', 'Quotes created', 'FileText', 0),
  ('sales', 'pending_quotations', 'Pending Quotations', 'Awaiting customer response', 'Clock3', 1),
  ('sales', 'approved_quotations', 'Approved Quotations', 'Accepted and converted', 'CheckCircle2', 2),
  ('sales', 'revenue', 'Revenue', 'Won value', 'DollarSign', 3),
  -- Invoice & Payments
  ('finance', 'invoices', 'Invoices', 'Invoices issued', 'Receipt', 0),
  ('finance', 'payments', 'Payments', 'Payments received', 'CreditCard', 1),
  ('finance', 'outstanding', 'Outstanding Invoices', 'Unpaid and overdue', 'AlertCircle', 2),
  ('finance', 'cashflow', 'Cash Flow', 'Money in vs out', 'ArrowLeftRight', 3),
  ('finance', 'profit', 'Profit', 'Margin and net profit', 'TrendingUp', 4),
  -- Meetings & Calendar
  ('meetings', 'today_meetings', 'Today''s Meetings', 'Scheduled meetings', 'CalendarDays', 0),
  ('meetings', 'calendar', 'Calendar', 'Monthly overview', 'Calendar', 1),
  ('meetings', 'ai_summaries', 'AI Summaries', 'Auto-generated summaries', 'Sparkles', 2),
  ('meetings', 'action_items', 'Action Items', 'Extracted tasks and owners', 'ListChecks', 3),
  -- Document Intelligence
  ('documents', 'ocr_queue', 'OCR Queue', 'Documents waiting for OCR', 'ScanText', 0),
  ('documents', 'recent_documents', 'Recent Documents', 'Latest uploads', 'FileText', 1),
  ('documents', 'knowledge_base', 'Knowledge Base', 'Company knowledge articles', 'BookOpen', 2),
  ('documents', 'ai_search', 'AI Search', 'Semantic document search', 'Search', 3),
  -- Task Management
  ('tasks', 'assigned_tasks', 'Assigned Tasks', 'Tasks assigned to members', 'ClipboardList', 0),
  ('tasks', 'due_tasks', 'Due Tasks', 'Tasks due soon', 'AlarmClock', 1),
  ('tasks', 'completed_tasks', 'Completed Tasks', 'Finished work', 'CheckCheck', 2),
  ('tasks', 'ai_reminders', 'AI Reminders', 'AI-scheduled reminders', 'Bell', 3),
  -- Workflow Automation
  ('workflows', 'running_workflows', 'Running Workflows', 'Active automations', 'PlayCircle', 0),
  ('workflows', 'failed_workflows', 'Failed Workflows', 'Automations with errors', 'XCircle', 1),
  ('workflows', 'automation_history', 'Automation History', 'Past runs and outcomes', 'History', 2),
  -- Reporting & Analytics
  ('reports', 'sales_reports', 'Sales Reports', 'Sales performance', 'BarChart3', 0),
  ('reports', 'revenue_reports', 'Revenue Reports', 'Revenue breakdown', 'DollarSign', 1),
  ('reports', 'customer_analytics', 'Customer Analytics', 'Cohorts and behavior', 'Users', 2),
  ('reports', 'employee_productivity', 'Employee Productivity', 'Output per member', 'Gauge', 3),
  ('reports', 'forecasting', 'Forecasting', 'Predictive projections', 'TrendingUp', 4),
  -- Integrations
  ('integrations', 'gmail', 'Gmail', 'Mail integration status', 'Mail', 0),
  ('integrations', 'outlook', 'Outlook', 'Microsoft 365 status', 'Briefcase', 1),
  ('integrations', 'whatsapp', 'WhatsApp', 'WhatsApp Business status', 'MessageCircle', 2),
  ('integrations', 'google_calendar', 'Google Calendar', 'Calendar sync status', 'Calendar', 3),
  ('integrations', 'microsoft365', 'Microsoft 365', '365 suite status', 'Briefcase', 4),
  ('integrations', 'api_status', 'API Status', 'Integration API health', 'Activity', 5),
  -- Notifications
  ('notifications', 'recent_notifications', 'Recent Notifications', 'Latest alerts', 'Bell', 0),
  ('notifications', 'email_alerts', 'Email Alerts', 'Email-based alerts', 'Mail', 1),
  ('notifications', 'whatsapp_alerts', 'WhatsApp Alerts', 'WhatsApp-based alerts', 'MessageCircle', 2),
  ('notifications', 'task_reminders', 'Task Reminders', 'Reminder notifications', 'AlarmClock', 3),
  -- Audit Logs
  ('audit', 'user_activity', 'User Activity', 'Human actions logged', 'UserCheck', 0),
  ('audit', 'ai_activity', 'AI Activity', 'Agent actions logged', 'Bot', 1),
  ('audit', 'login_history', 'Login History', 'Authentication events', 'LogIn', 2),
  ('audit', 'audit_logs', 'Audit Logs', 'Full audit trail', 'ScrollText', 3)
ON CONFLICT (module_key, widget_key) DO NOTHING;

-- =====================================================================
-- 3) BACKFILL org_modules for the newly added spec modules
-- =====================================================================
DO $$
DECLARE o RECORD;
BEGIN
    FOR o IN SELECT id FROM public.organizations LOOP
        PERFORM public.seed_org_modules(o.id);
    END LOOP;
END $$;
