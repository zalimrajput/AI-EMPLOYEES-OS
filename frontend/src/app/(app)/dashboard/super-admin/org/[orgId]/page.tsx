"use client";

import { useMemo } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowUpRight, Building2, Check, Globe2, Lock, Users } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchPlatformOrgs } from "@/services/admin";
import { DASHBOARDS } from "@/lib/dashboards";
import { MODULE_BY_KEY, isModuleEnabled, modulesForDashboard } from "@/lib/modules";
import { cn } from "@/lib/utils";

const PLAN_BADGE: Record<string, "default" | "accent" | "secondary"> = {
  Business: "default",
  Pro: "accent",
  Basic: "secondary",
  Trial: "secondary",
};

export default function OrgPreviewPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const { data: orgs, isLoading } = useQuery({
    queryKey: ["platform-orgs"],
    queryFn: fetchPlatformOrgs,
  });

  const org = orgs?.find((o) => o.id === orgId) ?? null;

  // The org's enabled modules — both flags must be on for a widget to show.
  const enabledModules = useMemo(() => {
    if (!org) return [];
    return org.modules
      .filter((m) => m.enabled_by_super_admin !== false && m.enabled_by_org_admin !== false)
      .map((m) => m.module_key);
  }, [org]);

  // Every company dashboard the org could use (super-admin is platform-only).
  const previewDashboards = useMemo(() => {
    return DASHBOARDS.filter((d) => d.id !== "super-admin");
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-40" />)}
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

  const enabledCount = enabledModules.length;

  return (
    <div className="space-y-8">
      <Link
        href="/dashboard/super-admin"
        className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="h-4 w-4" /> Back to all organizations
      </Link>

      <DashboardHeader
        eyebrow="Super admin · org preview"
        title={org.name}
        description={`Everything this company sees on AI Employee OS — dashboards and widgets for the ${enabledCount} modules enabled for their workspace. Click a dashboard to open it full screen.`}
        icon={Building2}
        gradient="from-danger to-warning"
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
            <Badge variant="accent"><Check className="h-3 w-3" /> {enabledCount}/{Object.keys(MODULE_BY_KEY).length} modules enabled</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Dashboard picker — click any card to open it full screen */}
      <div>
        <div className="mb-4 flex items-end justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white">Dashboards</h2>
            <p className="text-sm text-slate-500">
              {previewDashboards.length} role-based dashboards — open any of them full screen to inspect its widgets.
            </p>
          </div>
          <Badge variant="secondary" className="shrink-0">
            {previewDashboards.length} dashboards
          </Badge>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {previewDashboards.map((d, i) => {
            const Icon = d.icon;
            const modules = modulesForDashboard(d.name).filter((m) =>
              isModuleEnabled(enabledModules, m.key)
            );
            const widgetCount = modules.reduce((acc, m) => acc + m.widgets.length, 0);
            return (
              <motion.div
                key={d.id}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.04 }}
              >
                <Link href={`/dashboard/super-admin/org/${org.id}/${d.id}`} className="group block">
                  <Card className="h-full overflow-hidden transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10">
                    <CardHeader>
                      <div className="flex items-start justify-between gap-3">
                        <div className={cn("flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-lg", d.gradient)}>
                          <Icon className="h-5.5 w-5.5" />
                        </div>
                        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-card-soft text-slate-500 transition-all group-hover:bg-primary/15 group-hover:text-primary-soft">
                          <ArrowUpRight className="h-4 w-4" />
                        </span>
                      </div>
                      <CardTitle className="mt-3 text-base">{d.name}</CardTitle>
                      <CardDescription className="line-clamp-2">{d.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="flex items-center justify-between gap-2">
                      <Badge variant={modules.length > 0 ? "accent" : "secondary"}>
                        {modules.length} module{modules.length !== 1 ? "s" : ""} · {widgetCount} widgets
                      </Badge>
                      {modules.length === 0 && (
                        <span className="inline-flex items-center gap-1 text-[11px] text-slate-500">
                          <Lock className="h-3 w-3" /> Disabled
                        </span>
                      )}
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
