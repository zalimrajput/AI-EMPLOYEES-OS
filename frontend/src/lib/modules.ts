// Module registry for AI Employee OS.
// Mirrors supabase/migrations/0062 + 0063 (the `modules` + `widgets` seeds).
// Super Admin enables modules per organization (enabled_by_super_admin);
// Org Admin enables them for their own workspace (enabled_by_org_admin).
// A dashboard / widget area is visible only when its module is enabled for
// the organization AND the user's role grants access.
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  Briefcase,
  Building2,
  Calendar,
  CheckCircle2,
  ClipboardList,
  CreditCard,
  FileText,
  Headset,
  Kanban,
  KeyRound,
  LayoutDashboard,
  LogIn,
  Mail,
  Megaphone,
  MessageCircle,
  MessageSquare,
  MonitorSmartphone,
  PlayCircle,
  Plug,
  Receipt,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  UserCog,
  Users,
  Wallet,
  Workflow,
  Wrench,
  XCircle,
} from "lucide-react";

export interface WidgetDef {
  key: string;
  name: string;
  description: string;
  icon: LucideIcon;
}

export interface ModuleDef {
  key: string;
  name: string;
  description: string;
  icon: LucideIcon;
  group: "core" | "sales" | "finance" | "people" | "growth" | "operations" | "customer" | "productivity" | "admin";
  /** Dashboard the module powers (matches `modules.dashboard` seed). */
  dashboard: string | null;
  widgets: WidgetDef[];
}

const W = (key: string, name: string, description: string, icon: LucideIcon): WidgetDef => ({ key, name, description, icon });

export const MODULES: ModuleDef[] = [
  {
    key: "overview", name: "Overview", description: "Company-wide overview and quick stats.",
    icon: LayoutDashboard, group: "core", dashboard: "Company Admin Dashboard",
    widgets: [],
  },
  {
    key: "organization", name: "Organization Management", description: "Organizations, company settings, subscription, and storage usage.",
    icon: Building2, group: "admin", dashboard: "Company Admin Dashboard",
    widgets: [
      W("orgs", "Organizations", "Companies under this account", Building2),
      W("company_settings", "Company Settings", "Profile, branding, and defaults", Settings),
      W("subscription", "Subscription", "Plan, renewal, and status", CreditCard),
      W("storage", "Storage Usage", "Used vs allocated storage", FileText),
    ],
  },
  {
    key: "users_roles", name: "User & Role Management", description: "Users, departments, roles, and permissions.",
    icon: Users, group: "admin", dashboard: "Company Admin Dashboard",
    widgets: [
      W("users", "Users", "Team members and invitations", Users),
      W("departments", "Departments", "Structure and membership", Building2),
      W("roles", "Roles", "Role definitions and permissions", ShieldCheck),
      W("permissions", "Permissions", "Granular access matrix", KeyRound),
    ],
  },
  {
    key: "security", name: "Authentication & Security", description: "Login history, MFA status, active sessions, and security alerts.",
    icon: ShieldCheck, group: "admin", dashboard: "Company Admin Dashboard",
    widgets: [
      W("login_history", "Login History", "Recent sign-ins", LogIn),
      W("mfa_status", "MFA Status", "Two-factor enrollment", ShieldCheck),
      W("active_sessions", "Active Sessions", "Live sessions and devices", MonitorSmartphone),
      W("security_alerts", "Security Alerts", "Suspicious activity", AlertTriangle),
    ],
  },
  {
    key: "executive", name: "AI Executive Assistant", description: "AI tasks completed, pending approvals, insights, and business forecast.",
    icon: Sparkles, group: "core", dashboard: "CEO / Executive Dashboard",
    widgets: [
      W("ai_tasks_done", "AI Tasks Completed", "Work finished by AI", CheckCircle2),
      W("pending_approvals", "Pending Approvals", "Items awaiting approval", Sparkles),
      W("ai_insights", "AI Insights", "Automated business insights", Sparkles),
      W("forecast", "Business Forecast", "Projected performance", TrendingUp),
    ],
  },
  {
    key: "ai_employees", name: "AI Employees", description: "Active AI agents, AI requests, success rate, tool usage, and memory.",
    icon: Bot, group: "core", dashboard: "AI Employees Dashboard",
    widgets: [
      W("active_agents", "Active AI Agents", "Employees currently online", Bot),
      W("ai_requests", "AI Requests", "Requests handled this period", Activity),
      W("success_rate", "Success Rate", "Completed vs attempted", Target),
      W("tool_usage", "Tool Usage", "Tools called by agents", Wrench),
    ],
  },
  {
    key: "email", name: "Email Management", description: "Email queue, drafts, follow-ups, and email analytics.",
    icon: Mail, group: "customer", dashboard: "Customer Support Dashboard",
    widgets: [
      W("email_queue", "Email Queue", "Outbound messages pending", Mail),
      W("drafts", "Drafts", "Unsent drafts", FileText),
      W("followups", "Follow-ups", "Scheduled follow-ups", Mail),
      W("email_analytics", "Email Analytics", "Open, reply, and bounce rates", BarChart3),
    ],
  },
  {
    key: "whatsapp", name: "WhatsApp Communication", description: "WhatsApp chats, response time, satisfaction, and open conversations.",
    icon: MessageCircle, group: "customer", dashboard: "Customer Support Dashboard",
    widgets: [
      W("whatsapp_chats", "WhatsApp Chats", "Conversations and threads", MessageCircle),
      W("response_time", "Response Time", "Avg reply latency", Activity),
      W("satisfaction", "Customer Satisfaction", "CSAT scores", Target),
      W("open_conversations", "Open Conversations", "Chats needing attention", MessageSquare),
    ],
  },
  {
    key: "crm", name: "CRM", description: "Customers, new leads, sales pipeline, customer timeline, and AI summaries.",
    icon: Users, group: "sales", dashboard: "CRM Dashboard",
    widgets: [
      W("customers", "Customers", "Total customers and value", Users),
      W("new_leads", "New Leads", "Leads captured this period", Users),
      W("pipeline", "Sales Pipeline", "Deals by stage", TrendingUp),
      W("customer_timeline", "Customer Timeline", "Interaction history", Calendar),
      W("ai_customer_summary", "AI Customer Summary", "AI-generated relationship insights", Sparkles),
    ],
  },
  {
    key: "sales", name: "Quotation Management", description: "Quotations, pending and approved quotations, and revenue.",
    icon: TrendingUp, group: "sales", dashboard: "Sales Dashboard",
    widgets: [
      W("quotations", "Quotations", "Quotes created", FileText),
      W("pending_quotations", "Pending Quotations", "Awaiting customer response", FileText),
      W("approved_quotations", "Approved Quotations", "Accepted and converted", CheckCircle2),
      W("revenue", "Revenue", "Won value", TrendingUp),
    ],
  },
  {
    key: "finance", name: "Invoice & Payments", description: "Invoices, payments, outstanding invoices, cash flow, and profit.",
    icon: Wallet, group: "finance", dashboard: "Finance Dashboard",
    widgets: [
      W("invoices", "Invoices", "Invoices issued", Receipt),
      W("payments", "Payments", "Payments received", CreditCard),
      W("outstanding", "Outstanding Invoices", "Unpaid and overdue", AlertTriangle),
      W("cashflow", "Cash Flow", "Money in vs out", TrendingUp),
      W("profit", "Profit", "Margin and net profit", Wallet),
    ],
  },
  {
    key: "meetings", name: "Meetings & Calendar", description: "Today's meetings, calendar, AI summaries, and action items.",
    icon: Calendar, group: "productivity", dashboard: "Operations Dashboard",
    widgets: [
      W("today_meetings", "Today's Meetings", "Scheduled meetings", Calendar),
      W("calendar", "Calendar", "Monthly overview", Calendar),
      W("ai_summaries", "AI Summaries", "Auto-generated summaries", Sparkles),
      W("action_items", "Action Items", "Extracted tasks and owners", ClipboardList),
    ],
  },
  {
    key: "documents", name: "Document Intelligence", description: "OCR queue, recent documents, knowledge base, and AI search.",
    icon: FileText, group: "productivity", dashboard: "Operations Dashboard",
    widgets: [
      W("ocr_queue", "OCR Queue", "Documents waiting for OCR", FileText),
      W("recent_documents", "Recent Documents", "Latest uploads", FileText),
      W("knowledge_base", "Knowledge Base", "Company knowledge articles", BookOpen),
      W("ai_search", "AI Search", "Semantic document search", Search),
    ],
  },
  {
    key: "tasks", name: "Task Management", description: "Assigned tasks, due tasks, completed tasks, and AI reminders.",
    icon: Kanban, group: "operations", dashboard: "Employee Dashboard",
    widgets: [
      W("assigned_tasks", "Assigned Tasks", "Tasks assigned to members", ClipboardList),
      W("due_tasks", "Due Tasks", "Tasks due soon", Kanban),
      W("completed_tasks", "Completed Tasks", "Finished work", CheckCircle2),
      W("ai_reminders", "AI Reminders", "AI-scheduled reminders", Bell),
    ],
  },
  {
    key: "workflows", name: "Workflow Automation", description: "Running workflows, failed workflows, and automation history.",
    icon: Workflow, group: "operations", dashboard: "Operations Dashboard",
    widgets: [
      W("running_workflows", "Running Workflows", "Active automations", PlayCircle),
      W("failed_workflows", "Failed Workflows", "Automations with errors", XCircle),
      W("automation_history", "Automation History", "Past runs and outcomes", Activity),
    ],
  },
  {
    key: "reports", name: "Reporting & Analytics", description: "Sales reports, revenue reports, customer analytics, employee productivity, and forecasting.",
    icon: BarChart3, group: "operations", dashboard: "Reports & Analytics Dashboard",
    widgets: [
      W("sales_reports", "Sales Reports", "Sales performance", BarChart3),
      W("revenue_reports", "Revenue Reports", "Revenue breakdown", Wallet),
      W("customer_analytics", "Customer Analytics", "Cohorts and behavior", Users),
      W("employee_productivity", "Employee Productivity", "Output per member", UserCog),
      W("forecasting", "Forecasting", "Predictive projections", TrendingUp),
    ],
  },
  {
    key: "integrations", name: "Integrations", description: "Gmail, Outlook, WhatsApp, Google Calendar, Microsoft 365, and API status.",
    icon: Plug, group: "admin", dashboard: "Company Admin Dashboard",
    widgets: [
      W("gmail", "Gmail", "Mail integration status", Mail),
      W("outlook", "Outlook", "Microsoft 365 status", Briefcase),
      W("whatsapp", "WhatsApp", "WhatsApp Business status", MessageCircle),
      W("google_calendar", "Google Calendar", "Calendar sync status", Calendar),
      W("microsoft365", "Microsoft 365", "365 suite status", Briefcase),
      W("api_status", "API Status", "Integration API health", Activity),
    ],
  },
  {
    key: "notifications", name: "Notifications", description: "Recent notifications, email alerts, WhatsApp alerts, and task reminders.",
    icon: Bell, group: "core", dashboard: null,
    widgets: [
      W("recent_notifications", "Recent Notifications", "Latest alerts", Bell),
      W("email_alerts", "Email Alerts", "Email-based alerts", Mail),
      W("whatsapp_alerts", "WhatsApp Alerts", "WhatsApp-based alerts", MessageCircle),
      W("task_reminders", "Task Reminders", "Reminder notifications", Bell),
    ],
  },
  {
    key: "audit", name: "Audit Logs", description: "User activity, AI activity, login history, and audit logs.",
    icon: ShieldCheck, group: "admin", dashboard: "Company Admin Dashboard",
    widgets: [
      W("user_activity", "User Activity", "Human actions logged", Users),
      W("ai_activity", "AI Activity", "Agent actions logged", Bot),
      W("login_history", "Login History", "Authentication events", LogIn),
      W("audit_logs", "Audit Logs", "Full audit trail", FileText),
    ],
  },
  {
    key: "hr", name: "HR & People", description: "Employees, attendance, and hiring.",
    icon: UserCog, group: "people", dashboard: "HR Dashboard",
    widgets: [
      W("employees", "Employees", "Team roster", Users),
      W("attendance", "Attendance", "Presence overview", UserCog),
      W("hiring", "Hiring", "Candidates and pipeline", UserCog),
    ],
  },
  {
    key: "marketing", name: "Marketing", description: "Campaigns, content, and audience.",
    icon: Megaphone, group: "growth", dashboard: "Marketing Dashboard",
    widgets: [
      W("campaigns", "Campaigns", "Active and planned", Megaphone),
      W("content", "Content", "Drafts and published", FileText),
      W("audience", "Audience", "Segments and reach", Users),
    ],
  },
  {
    key: "operations", name: "Operations", description: "Tasks, workflows, and daily operations.",
    icon: Workflow, group: "operations", dashboard: "Operations Dashboard",
    widgets: [
      W("daily_ops", "Daily Operations", "Workload overview", Workflow),
      W("sla", "SLA Health", "SLA adherence", Target),
    ],
  },
  {
    key: "support", name: "Customer Support", description: "Email, WhatsApp, and tickets.",
    icon: Headset, group: "customer", dashboard: "Customer Support Dashboard",
    widgets: [
      W("tickets", "Tickets", "Open and resolved", Headset),
      W("channels", "Channels", "Email and WhatsApp", MessageCircle),
    ],
  },
  {
    key: "billing", name: "Billing", description: "Subscriptions, usage, and payments.",
    icon: CreditCard, group: "admin", dashboard: "Company Admin Dashboard",
    widgets: [
      W("plan", "Plan", "Current subscription", CreditCard),
      W("usage", "Usage", "AI request consumption", Activity),
      W("invoices_billing", "Invoices", "Billing history", Receipt),
    ],
  },
  {
    key: "settings", name: "Settings", description: "Organization settings and integrations.",
    icon: Settings, group: "admin", dashboard: "Settings & Integrations Dashboard",
    widgets: [
      W("org_settings", "Organization Settings", "Profile and defaults", Settings),
      W("integrations_settings", "Integrations", "Connected applications", Plug),
    ],
  },
];

/** Fast lookup keyed by module key. */
export const MODULE_BY_KEY: Record<string, ModuleDef> = Object.fromEntries(
  MODULES.map((m) => [m.key, m])
);

/**
 * Modules an admin can toggle on/off. The "overview" module is always on —
 * it backs the main dashboard and login landing, so it can't be disabled.
 */
export const TOGGLEABLE_MODULES = MODULES.filter((m) => m.key !== "overview");

/** Dashboard id -> module key (dashboards seeded in 0060, modules in 0063). */
const DASHBOARD_MODULE: Record<string, string> = {
  "super-admin": "overview",
  "company-admin": "overview",
  executive: "executive",
  sales: "sales",
  crm: "crm",
  hr: "hr",
  finance: "finance",
  support: "support",
  marketing: "marketing",
  operations: "operations",
  employee: "tasks",
  "ai-employees": "ai_employees",
  reports: "reports",
  settings: "settings",
};

/** Nav route -> module key. */
const NAV_MODULE: Record<string, string> = {
  "/dashboard": "overview",
  "/dashboard/employees": "ai_employees",
  "/dashboard/tasks": "tasks",
  "/dashboard/workflows": "workflows",
  "/dashboard/analytics": "reports",
  "/dashboard/chat": "ai_employees",
  "/dashboard/billing": "billing",
  "/dashboard/settings": "settings",
};

/**
 * Whether a module is enabled for the org.
 * - `undefined`/`null` means no module data (super admin / legacy org) —
 *   treat everything as enabled.
 * - an empty array means the org has module rows but ALL are disabled —
 *   nothing is enabled.
 * - an array is the set of enabled module keys.
 */
export function isModuleEnabled(
  enabledModules: string[] | undefined | null,
  key: string | undefined | null
): boolean {
  if (!key) return true;
  if (!enabledModules) return true; // no module data — legacy/fresh org or super admin
  return enabledModules.includes(key);
}

/** Module key for a dashboard id (undefined for unlisted dashboards). */
export function moduleKeyFor(dashboardId: string): string | undefined {
  return DASHBOARD_MODULE[dashboardId];
}

/** Filter dashboards by the org's enabled modules. */
export function dashboardsForModules<T extends { id: string }>(
  dashboards: T[],
  enabledModules: string[] | undefined | null
): T[] {
  return dashboards.filter((d) =>
    isModuleEnabled(enabledModules, DASHBOARD_MODULE[d.id])
  );
}

/** Filter nav items by the org's enabled modules. */
export function navForModules<T extends { href: string }>(
  items: T[],
  enabledModules: string[] | undefined | null
): T[] {
  return items.filter((i) =>
    isModuleEnabled(enabledModules, NAV_MODULE[i.href])
  );
}

/** Modules that power a given dashboard name (mirrors `modules.dashboard`). */
export function modulesForDashboard(dashboardName: string | null | undefined): ModuleDef[] {
  if (!dashboardName) return MODULES.filter((m) => m.dashboard === null);
  return MODULES.filter((m) => m.dashboard === dashboardName);
}
