"use client";

import { cn } from "@/lib/utils";
import {
  Bot,
  ChevronLeft,
  ChevronsUpDown,
  LayoutDashboard,
  Settings,
  Workflow,
  BarChart3,
  MessageSquare,
  CreditCard,
  Kanban,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Avatar } from "@/components/ui/avatar";
import { Logo } from "@/components/shared/logo";
import type { SessionUser } from "@/hooks/use-session";
import { ADMIN_ONLY_PATHS, ROLES, ROLE_META, isAdmin, primaryRole } from "@/lib/roles";
import { DASHBOARDS, dashboardsForRoles } from "@/lib/dashboards";
import { dashboardsForModules, navForModules } from "@/lib/modules";

export const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/employees", label: "AI Employees", icon: Bot },
  { href: "/dashboard/tasks", label: "Tasks", icon: Kanban },
  { href: "/dashboard/workflows", label: "Workflows", icon: Workflow },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/dashboard/chat", label: "AI Chat", icon: MessageSquare },
  { href: "/dashboard/billing", label: "Billing", icon: CreditCard },
];

export function Sidebar({
  collapsed,
  onToggle,
  user,
  onMobileClose,
}: {
  collapsed: boolean;
  onToggle: () => void;
  user: SessionUser | null;
  onMobileClose?: () => void;
}) {
  const pathname = usePathname();
  const admin = isAdmin(user?.roles);
  const userRole = primaryRole(user?.roles);

  const enabledModules = user?.enabledModules;
  // Role-filtered nav (ADMIN_ONLY_PATHS) then module-filtered (org settings).
  const visibleItems = navForModules(
    NAV_ITEMS.filter(({ href }) =>
      admin || !ADMIN_ONLY_PATHS.some((path) => href.startsWith(path))
    ),
    enabledModules
  );
  // Role-scoped dashboard list in the side panel:
  // - Super Admin keeps a single quick link to their own platform dashboard;
  //   every company dashboard is reached through the org browser.
  // - Company Admin / CEO see all 13 company dashboards for their own org.
  // - Every other role sees exactly the dashboards their role can open.
  // The list is filtered by the org's enabled modules either way.
  const isSuperAdmin = user?.roles?.includes(ROLES.SUPER_ADMIN) ?? false;
  const dashboards = isSuperAdmin
    ? DASHBOARDS.filter((d) => d.id === "super-admin")
    : dashboardsForModules(dashboardsForRoles(user?.roles), enabledModules).filter(
        // The Company Admin dashboard is the main-nav "Dashboard" item
        // (/dashboard) — skip it here so org admins don't see it twice.
        (d) => d.href !== "/dashboard"
      );
  const showDashboards = dashboards.length > 0;
  const showSettings = admin;

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 76 : 260 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="relative z-30 hidden h-full shrink-0 flex-col border-r border-border-soft bg-card/60 backdrop-blur-xl md:flex"
    >
      <div className={cn("flex items-center gap-3 px-4", collapsed ? "justify-center py-5" : "py-5")}>
        <Logo size="sm" iconOnly={collapsed} />
        {!collapsed && <Logo size="sm" className="hidden" />}
        {!collapsed && (
          <span className="text-sm font-bold tracking-tight text-white">
            AI <span className="text-gradient">Employee OS</span>
          </span>
        )}
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2 no-scrollbar">
        {visibleItems.map(({ href, label, icon: Icon }) => {
          const active =
            pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link key={href} href={href} onClick={onMobileClose} className="block relative">
              {active && (
                <motion.span
                  layoutId="nav-active"
                  className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary/25 to-secondary/25 border border-primary/30"
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
              )}
              <span
                className={cn(
                  "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors",
                  collapsed && "justify-center px-0",
                  active ? "text-white" : "text-slate-400 hover:text-white hover:bg-card-soft"
                )}
              >
                <Icon className={cn("h-[18px] w-[18px] shrink-0", active && "text-primary-soft")} />
                {!collapsed && <span>{label}</span>}
                {!collapsed && active && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-gradient-to-r from-primary to-accent animate-pulse-glow" />
                )}
              </span>
            </Link>
          );
        })}

        {showDashboards && (
          <div className="pt-3">
            <p className="px-3 pb-2 text-[10px] font-bold uppercase tracking-widest text-slate-500">
              {collapsed ? "DB" : "Dashboards"}
            </p>
            <div className="space-y-1">
              {dashboards.map(({ href, name, icon: Icon }) => {
                const active =
                  pathname === href ||
                  (href !== "/dashboard" && pathname.startsWith(href));
                return (
                  <Link key={href} href={href} onClick={onMobileClose} className="relative block">
                    {active && (
                      <motion.span
                        layoutId="dash-active"
                        className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary/25 to-secondary/25 border border-primary/30"
                        transition={{ type: "spring", stiffness: 350, damping: 30 }}
                      />
                    )}
                    <span
                      className={cn(
                        "relative flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold transition-colors",
                        collapsed && "justify-center px-0",
                        active ? "text-white" : "text-slate-400 hover:text-white hover:bg-card-soft"
                      )}
                      title={name}
                    >
                      <Icon className={cn("h-4 w-4 shrink-0", active && "text-primary-soft")} />
                      {!collapsed && <span className="truncate">{name.replace(/ Dashboard$/, "")}</span>}
                      {!collapsed && active && (
                        <span className="ml-auto h-1.5 w-1.5 shrink-0 rounded-full bg-gradient-to-r from-primary to-accent animate-pulse-glow" />
                      )}
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        )}

        {showSettings && (
          <div className="pt-3">
            <Link
              href="/dashboard/settings"
              onClick={onMobileClose}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors",
                collapsed && "justify-center px-0",
                pathname.startsWith("/dashboard/settings")
                  ? "text-white bg-card-soft"
                  : "text-slate-400 hover:text-white hover:bg-card-soft"
              )}
            >
              <Settings className="h-[18px] w-[18px] shrink-0" />
              {!collapsed && <span>Settings</span>}
            </Link>
          </div>
        )}
      </nav>

      {/* Workspace selector + profile */}
      <div className="border-t border-border-soft p-3">
        <button
          onClick={onToggle}
          className={cn(
            "mb-2 flex w-full items-center gap-2 rounded-xl px-2 py-1.5 text-xs text-slate-500 transition-colors hover:bg-card-soft hover:text-slate-300",
            collapsed && "justify-center"
          )}
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform duration-300", collapsed && "rotate-180")} />
          {!collapsed && <span className="font-semibold">Collapse</span>}
        </button>

        <div
          className={cn(
            "flex items-center gap-3 rounded-xl border border-border-soft bg-card-soft/60 p-2.5",
            collapsed && "justify-center"
          )}
        >
          <Avatar name={user?.orgName || "AI"} size="sm" />
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-bold text-white">{user?.orgName ?? "My Workspace"}</p>
              <p className="truncate text-xs text-slate-500">{user?.email ?? "Sign in to continue"}</p>
            </div>
          )}
          {!collapsed && userRole && (
            <span
              title={ROLE_META[userRole].description}
              className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${ROLE_META[userRole].badgeClass}`}
            >
              {ROLE_META[userRole].label}
            </span>
          )}
          {!collapsed && <ChevronsUpDown className="h-4 w-4 shrink-0 text-slate-500" />}
        </div>
      </div>
    </motion.aside>
  );
}
