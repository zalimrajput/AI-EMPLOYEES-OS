"use client";

import { ArrowRight, Compass, Lock } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { ModuleWidgets } from "@/components/dashboard/module-widgets";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DASHBOARDS, dashboardsForRoles } from "@/lib/dashboards";
import { dashboardsForModules } from "@/lib/modules";
import { useSession } from "@/hooks/use-session";
import { ROLE_META, primaryRole } from "@/lib/roles";
import { cn } from "@/lib/utils";

const GROUP_LABELS: Record<string, string> = {
  platform: "Platform",
  company: "Leadership",
  department: "Departments",
  personal: "Personal",
  system: "System",
};

export default function DashboardsHubPage() {
  const { data: session } = useSession();
  const roles = session?.user?.roles;
  const enabledModules = session?.user?.enabledModules;
  // Role access AND org module enablement both gate visibility.
  const accessible = dashboardsForModules(
    dashboardsForRoles(roles),
    enabledModules
  );
  const userRole = primaryRole(roles);

  const groups = ["platform", "company", "department", "personal", "system"] as const;

  return (
    <div className="space-y-8">
      <DashboardHeader
        eyebrow="Workspace hub"
        title="All Dashboards"
        description="Every dashboard available on AI Employee OS — organized by role and department. Locked ones are disabled until your role gains access."
        icon={Compass}
        gradient="from-primary to-accent"
      />

      {userRole && (
        <div className="flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/10 px-4 py-3 text-sm">
          <span className="font-semibold text-primary-soft">Your primary role:</span>
          <Badge variant="default">{ROLE_META[userRole]?.label ?? userRole}</Badge>
          <span className="ml-2 text-slate-400">
            — you can open <span className="font-bold text-white">{accessible.length}</span> of {DASHBOARDS.length} dashboards.
          </span>
        </div>
      )}

      {/* Global widgets (notifications) are shown regardless of dashboard */}
      <ModuleWidgets
        dashboardName={null}
        title="Global widgets"
        description="Areas available across every dashboard — gated by your org's enabled modules."
      />

      {groups.map((group) => {
        const dashboards = DASHBOARDS.filter((d) => d.group === group);
        if (dashboards.length === 0) return null;
        return (
          <div key={group}>
            <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">
              {GROUP_LABELS[group]}
            </h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {dashboards.map((d, i) => {
                const allowed = accessible.some((a) => a.id === d.id);
                const Icon = d.icon;
                return (
                  <motion.div
                    key={d.id}
                    initial={{ opacity: 0, y: 16 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.05 }}
                    whileHover={allowed ? { y: -6 } : undefined}
                  >
                    <Link href={d.href} aria-disabled={!allowed} className={cn("block h-full", !allowed && "pointer-events-none opacity-50")}>
                      <Card className="h-full overflow-hidden transition-colors hover:border-primary/40">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className={cn("flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-lg", d.gradient)}>
                              <Icon className="h-5.5 w-5.5" />
                            </div>
                            {!allowed && <Lock className="h-4 w-4 text-slate-500" />}
                          </div>
                          <CardTitle className="mt-3">{d.name}</CardTitle>
                          <CardDescription>{d.description}</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="flex flex-wrap gap-1.5">
                            {d.roles.map((r) => (
                              <span key={r} className="rounded-full border border-border-soft bg-card-soft px-2 py-0.5 text-[10px] font-semibold text-slate-400">
                                {ROLE_META[r]?.label ?? r}
                              </span>
                            ))}
                          </div>
                          {allowed && (
                            <p className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-primary-soft hover:text-white transition-colors">
                              Open dashboard <ArrowRight className="h-3.5 w-3.5" />
                            </p>
                          )}
                        </CardContent>
                      </Card>
                    </Link>
                  </motion.div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
