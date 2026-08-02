"use client";

import { useSession } from "@/hooks/use-session";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { MobileBottomNav } from "@/components/layout/mobile-nav";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { motion } from "framer-motion";
import { ADMIN_ONLY_PATHS, isAdmin } from "@/lib/roles";
import { DASHBOARDS, dashboardsForRoles, safeHomePathForRoles } from "@/lib/dashboards";
import { isModuleEnabled, moduleKeyFor } from "@/lib/modules";
import { usePathname } from "next/navigation";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { data, isLoading } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (isLoading) return;
    if (!data?.session) {
      router.replace("/login");
      return;
    }
    const roles = data.user?.roles;
    const enabledModules = data.user?.enabledModules;
    // Redirect target that passes BOTH the role check and the module gate,
    // so a user whose home dashboard's module is disabled never loops.
    const fallback = safeHomePathForRoles(roles, enabledModules);
    // Role guard 1: Employees are redirected away from admin-only sections.
    if (!isAdmin(roles) && ADMIN_ONLY_PATHS.some((p) => pathname.startsWith(p))) {
      router.replace(fallback);
      return;
    }
    // Role guard 2: Dashboard pages are only open to roles with access
    // (mirrors dashboard_role_access in the DB) AND to orgs where the
    // dashboard's module is enabled. Uses segment-boundary matching so
    // "/dashboard/employees" doesn't collide with "/dashboard/employee".
    const dashboard = DASHBOARDS.find(
      (d) =>
        d.href !== "/dashboard" &&
        (pathname === d.href || pathname.startsWith(`${d.href}/`))
    );
    if (dashboard) {
      const roleAllowed = dashboardsForRoles(roles).some((d) => d.id === dashboard.id);
      const moduleAllowed = isModuleEnabled(enabledModules, moduleKeyFor(dashboard.id));
      if (!roleAllowed || !moduleAllowed) {
        router.replace(fallback);
      }
    }
  }, [isLoading, data, pathname, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col p-6 gap-4">
        <Skeleton className="h-16 w-full" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} user={data?.user ?? null} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Navbar user={data?.user ?? null} />
        <motion.main
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          className="flex-1 overflow-y-auto px-4 py-6 md:px-8 md:py-8 pb-24 md:pb-8"
        >
          {children}
        </motion.main>
      </div>
      <MobileBottomNav user={data?.user ?? null} />
    </div>
  );
}
