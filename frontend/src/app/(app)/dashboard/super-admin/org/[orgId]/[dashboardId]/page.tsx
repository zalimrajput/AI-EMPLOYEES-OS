"use client";

import { useMemo } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowUpRight, Building2, Check, Globe2, Lock, Users } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { ModuleWidgets } from "@/components/dashboard/module-widgets";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchPlatformOrgs } from "@/services/admin";
import { DASHBOARDS } from "@/lib/dashboards";
import { isModuleEnabled, modulesForDashboard } from "@/lib/modules";
import { cn } from "@/lib/utils";

const PLAN_BADGE: Record<string, "default" | "accent" | "secondary"> = {
  Business: "default",
  Pro: "accent",
  Basic: "secondary",
  Trial: "secondary",
};

export default function OrgDashboardPreviewPage() {
  const { orgId, dashboardId } = useParams<{ orgId: string; dashboardId: string }>();
  const { data: orgs, isLoading } = useQuery({
    queryKey: ["platform-orgs"],
    queryFn: fetchPlatformOrgs,
  });

  const org = orgs?.find((o) => o.id === orgId) ?? null;
  const dashboard = DASHBOARDS.find((d) => d.id === dashboardId) ?? null;

  // The org's enabled modules — both flags must be on for a widget to show.
  const enabledModules = useMemo(() => {
    if (!org) return [];
    return org.modules
      .filter((m) => m.enabled_by_super_admin !== false && m.enabled_by_org_admin !== false)
      .map((m) => m.module_key);
  }, [org]);

  const enabledModuleCount = useMemo(() => {
    if (!dashboard) return 0;
    return modulesForDashboard(dashboard.name).filter((m) =>
      isModuleEnabled(enabledModules, m.key)
    ).length;
  }, [dashboard, enabledModules]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => <Skeleton key={i} className="h-48" />)}
        </div>
      </div>
    );
  }

  if (!org) {
    return (
      <div className="rounded-2xl border border-danger/30 bg-danger/10 p-10 text-center">
        <p className="font-bold text-danger">Organization not found</p>
        <Link href="/dashboard/super-admin" className="mt-2 inline-block text-sm text-primary-soft hover:underline">
          ← Back to all organizations
        </Link>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="rounded-2xl border border-danger/30 bg-danger/10 p-10 text-center">
        <p className="font-bold text-danger">Dashboard not found</p>
        <Link
          href={`/dashboard/super-admin/org/${org.id}`}
          className="mt-2 inline-block text-sm text-primary-soft hover:underline"
        >
          ← Back to {org.name} dashboards
        </Link>
      </div>
    );
  }

  const Icon = dashboard.icon;
  const isEnabled = enabledModuleCount > 0;

  return (
    <div className="space-y-8">
      <Link
        href={`/dashboard/super-admin/org/${org.id}`}
        className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="h-4 w-4" /> Back to {org.name} dashboards
      </Link>

      <DashboardHeader
        eyebrow="Super admin · org preview"
        title={dashboard.name}
        description={`How this dashboard renders for ${org.name} — ${enabledModuleCount} enabled module${enabledModuleCount !== 1 ? "s" : ""} gated by the company's workspace settings.`}
        icon={Icon}
        gradient={dashboard.gradient}
        actions={
          <div className="flex items-center gap-2">
            <Badge variant={org.status === "active" ? "success" : "warning"}>{org.status}</Badge>
            <Badge variant={PLAN_BADGE[org.plan] ?? "secondary"}>{org.plan}</Badge>
          </div>
        }
      />

      {/* Org summary */}
      <Card>
        <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <Avatar name={org.name} size="lg" />
            <div>
              <p className="text-sm font-bold text-white">{org.name}</p>
              <p className="text-xs text-slate-500">
                {org.industry ?? "—"} · {org.country ?? "—"} · created {new Date(org.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary"><Users className="h-3 w-3" /> {org.users} users</Badge>
            <Badge variant="secondary"><Globe2 className="h-3 w-3" /> {org.slug}</Badge>
            <Badge variant={isEnabled ? "accent" : "warning"}>
              <Check className="h-3 w-3" /> {enabledModuleCount} enabled
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Full-screen widget layout */}
      {isEnabled ? (
        <ModuleWidgets
          dashboardName={dashboard.name}
          enabledModules={enabledModules}
          title="Widgets"
          description={`Gated by the modules this company has enabled — ${org.name} sees exactly this.`}
        />
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center gap-3 rounded-2xl border border-border-soft bg-card-soft/40 px-6 py-14 text-center"
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-card-soft">
            <Lock className="h-5.5 w-5.5 text-slate-500" />
          </span>
          <p className="text-sm font-bold text-white">No modules enabled for this dashboard</p>
          <p className="max-w-sm text-xs text-slate-500">
            {org.name} has not enabled any modules that power the {dashboard.name}. Enable one from the module manager
            and it will appear here.
          </p>
          <Link
            href={`/dashboard/super-admin/org/${org.id}`}
            className="mt-1 inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-primary to-secondary px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-primary/25 transition-all hover:shadow-primary/40"
          >
            Browse dashboards <ArrowUpRight className="h-4 w-4" />
          </Link>
        </motion.div>
      )}

      {/* All modules that power this dashboard, for context */}
      {dashboard && (
        <Card>
          <CardHeader>
            <CardTitle>Modules powering this dashboard</CardTitle>
            <CardDescription>{dashboard.name} maps to these modules — enabled ones show their widgets above.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {modulesForDashboard(dashboard.name).map((m) => {
              const enabled = isModuleEnabled(enabledModules, m.key);
              const Icon2 = m.icon;
              return (
                <div
                  key={m.key}
                  className={cn(
                    "flex items-center gap-3 rounded-xl border p-3",
                    enabled ? "border-primary/30 bg-primary/10" : "border-border-soft bg-card-soft/40 opacity-60"
                  )}
                >
                  <span
                    className={cn(
                      "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
                      enabled ? "bg-gradient-to-br from-primary to-accent text-white" : "bg-card-soft text-slate-500"
                    )}
                  >
                    <Icon2 className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-bold text-white">{m.name}</p>
                    <p className="truncate text-xs text-slate-500">{m.widgets.length} widgets</p>
                  </div>
                  <Badge variant={enabled ? "success" : "secondary"}>
                    {enabled ? (
                      <>
                        <Check className="h-3 w-3" /> On
                      </>
                    ) : (
                      "Off"
                    )}
                  </Badge>
                </div>
              );
            })}
            {modulesForDashboard(dashboard.name).length === 0 && (
              <p className="col-span-full text-sm text-slate-500">
                No modules are registered for this dashboard yet.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Back to all dashboards */}
      <div className="flex justify-center">
        <Link
          href={`/dashboard/super-admin/org/${org.id}`}
          className="inline-flex items-center gap-1.5 rounded-xl border border-border-soft bg-card-soft/40 px-4 py-2.5 text-sm font-bold text-white transition-colors hover:border-primary/40 hover:bg-card-soft"
        >
          <Building2 className="h-4 w-4" /> View all {org.name} dashboards
        </Link>
      </div>
    </div>
  );
}
