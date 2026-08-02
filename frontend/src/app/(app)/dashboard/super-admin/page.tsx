"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bot,
  Building2,
  CreditCard,
  Globe2,
  LayoutDashboard,
  Plus,
  Plug,
  ShieldCheck,
  Sparkles,
  UserCheck,
  Wallet,
  X,
} from "lucide-react";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { StatCard } from "@/components/dashboard/stat-card";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchPlatformOrgs, fetchPlatformOverview, updateOrgMeta, updateOrgModule } from "@/services/admin";
import { MODULE_BY_KEY, TOGGLEABLE_MODULES } from "@/lib/modules";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

const PLAN_BADGE: Record<string, "default" | "accent" | "secondary"> = {
  Business: "default",
  Pro: "accent",
  Basic: "secondary",
  Trial: "secondary",
};

export default function SuperAdminDashboardPage() {
  const queryClient = useQueryClient();
  const { data: orgs, isLoading } = useQuery({
    queryKey: ["platform-orgs"],
    queryFn: fetchPlatformOrgs,
  });
  const { data: overview } = useQuery({
    queryKey: ["platform-overview"],
    queryFn: fetchPlatformOverview,
  });
  const [selectedOrg, setSelectedOrg] = useState<string | null>(null);

  const totals = useMemo(() => {
    const totalUsers = (orgs ?? []).reduce((acc, o) => acc + o.users, 0);
    const active = (orgs ?? []).filter((o) => o.status === "active").length;
    const business = (orgs ?? []).filter((o) => o.plan === "Business").length;
    return { totalUsers, active, business };
  }, [orgs]);

  async function toggleSuperAdminModule(orgId: string, moduleKey: string, enabled: boolean) {
    const { error } = await updateOrgModule(orgId, moduleKey, {
      enabled_by_super_admin: enabled,
    });
    if (error) {
      toast.error(error);
      return;
    }
    queryClient.invalidateQueries({ queryKey: ["platform-orgs"] });
    toast.success(`${enabled ? "Enabled" : "Disabled"} ${MODULE_BY_KEY[moduleKey]?.name ?? moduleKey}`);
  }

  async function changeOrgStatus(orgId: string, status: string) {
    const { error } = await updateOrgMeta(orgId, { status });
    if (error) return toast.error(error);
    queryClient.invalidateQueries({ queryKey: ["platform-orgs"] });
    toast.success(`Organization marked ${status}`);
  }

  const selected = orgs?.find((o) => o.id === selectedOrg) ?? null;

  return (
    <div className="space-y-8">
      <DashboardHeader
        eyebrow="Platform operations"
        title="Super Admin Dashboard"
        description="Every organization on AI Employee OS — tenants, plans, users, and the modules you enable for each company."
        icon={ShieldCheck}
        gradient="from-danger to-warning"
        actions={
          <Button variant="secondary" onClick={() => toast.info("Self-service signup is live — companies register their own admin at /register.")}>
            <Plus className="h-4 w-4" /> New company
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Companies" value={String(orgs?.length ?? 0)} delta={9} icon={<Building2 className="h-5 w-5" />} gradient="from-primary to-secondary" loading={isLoading} />
        <StatCard label="Active Tenants" value={String(totals.active)} delta={16} icon={<Globe2 className="h-5 w-5" />} gradient="from-secondary to-accent" loading={isLoading} />
        <StatCard label="Platform Users" value={String(totals.totalUsers)} delta={12} icon={<UserCheck className="h-5 w-5" />} gradient="from-accent to-success" loading={isLoading} />
        <StatCard label="Business Plans" value={String(totals.business)} delta={24} icon={<CreditCard className="h-5 w-5" />} gradient="from-warning to-danger" loading={isLoading} />
      </div>

      {/* Platform responsibilities — plans, AI models, integrations, templates */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Platform management</CardTitle>
            <CardDescription>Subscription plans, AI models, integrations, and dashboard templates across the platform</CardDescription>
          </div>
          <Badge variant="accent">
            <Wallet className="h-3 w-3" /> {overview?.plans.length ?? 0} plans
          </Badge>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {/* Subscription plans */}
            <div className="rounded-xl border border-border-soft bg-card-soft/40 p-4">
              <div className="flex items-center justify-between">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-secondary text-white">
                  <CreditCard className="h-4 w-4" />
                </span>
                <Badge variant="secondary">{overview?.plans.length ?? 0} active</Badge>
              </div>
              <p className="mt-3 text-sm font-bold text-white">Subscription plans</p>
              <div className="mt-2 space-y-1">
                {(overview?.plans ?? []).map((p) => (
                  <div key={p.id} className="flex items-center justify-between rounded-lg bg-card px-2.5 py-1.5 text-xs">
                    <span className="font-semibold text-slate-200">{p.name}</span>
                    <span className="text-slate-500">
                      ${p.price_monthly ?? 0}/mo{p.max_users ? ` · ${p.max_users} users` : " · Unlimited"}
                    </span>
                  </div>
                ))}
                {(overview?.plans ?? []).length === 0 && (
                  <p className="text-xs text-slate-500">No plans seeded yet.</p>
                )}
              </div>
            </div>

            {/* AI models */}
            <div className="rounded-xl border border-border-soft bg-card-soft/40 p-4">
              <div className="flex items-center justify-between">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-secondary to-accent text-white">
                  <Bot className="h-4 w-4" />
                </span>
                <Badge variant="secondary">{overview?.aiModels ?? 0} deployed</Badge>
              </div>
              <p className="mt-3 text-sm font-bold text-white">AI models</p>
              <p className="mt-1 text-xs text-slate-500">
                AI employees running across all tenants. Each company deploys its own specialized agents with model and tool settings.
              </p>
            </div>

            {/* Integrations */}
            <div className="rounded-xl border border-border-soft bg-card-soft/40 p-4">
              <div className="flex items-center justify-between">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-success text-white">
                  <Plug className="h-4 w-4" />
                </span>
                <Badge variant="secondary">{overview?.integrations ?? 0} connected</Badge>
              </div>
              <p className="mt-3 text-sm font-bold text-white">Integrations</p>
              <p className="mt-1 text-xs text-slate-500">
                Gmail, Outlook, WhatsApp Business, Google Calendar, Microsoft 365, and API connections companies have linked.
              </p>
            </div>

            {/* Dashboard templates */}
            <div className="rounded-xl border border-border-soft bg-card-soft/40 p-4">
              <div className="flex items-center justify-between">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-warning to-danger text-white">
                  <LayoutDashboard className="h-4 w-4" />
                </span>
                <Badge variant="secondary">{overview?.dashboards ?? 0} layouts</Badge>
              </div>
              <p className="mt-3 text-sm font-bold text-white">Dashboard templates</p>
              <p className="mt-1 text-xs text-slate-500">
                The 14 role-based dashboards each company gets, mapped to modules and seeded per tenant.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tenant list */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Organizations</CardTitle>
            <CardDescription>Every tenant on the platform with plan, status, and module control</CardDescription>
          </div>
          <Badge variant="accent"><Globe2 className="h-3 w-3" /> {orgs?.length ?? 0} tenants</Badge>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : (orgs ?? []).length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-500">
              No organizations yet. When a company registers, its admin appears here.
            </p>
          ) : (
            <div className="space-y-2">
              {(orgs ?? []).map((o, i) => (
                <motion.div
                  key={o.id}
                  initial={{ opacity: 0, y: 8 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.04 }}
                  whileHover={{ x: 4 }}
                  className="flex items-center gap-4 rounded-xl border border-border-soft bg-card-soft/40 p-4 transition-colors hover:border-primary/30"
                >
                  <Avatar name={o.name} size="md" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-bold text-white">{o.name}</p>
                    <p className="text-xs text-slate-500">{o.users} users · {o.country ?? "—"} · {new Date(o.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="hidden w-40 flex-col items-end gap-1 sm:flex">
                    <Badge variant={o.status === "active" ? "success" : "warning"}>{o.status}</Badge>
                    <Badge variant={PLAN_BADGE[o.plan] ?? "secondary"}>{o.plan}</Badge>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Link href={`/dashboard/super-admin/org/${o.id}`}>
                      <Button variant="secondary" size="sm">
                        <LayoutDashboard className="h-3.5 w-3.5" /> View dashboards
                      </Button>
                    </Link>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setSelectedOrg(o.id)}
                    >
                      <Sparkles className="h-3.5 w-3.5" /> Modules
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => changeOrgStatus(o.id, o.status === "active" ? "suspended" : "active")}
                    >
                      {o.status === "active" ? "Suspend" : "Activate"}
                    </Button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Per-org module manager */}
      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm sm:items-center"
            onClick={() => setSelectedOrg(null)}
          >
            <motion.div
              onClick={(e) => e.stopPropagation()}
              className="max-h-[88vh] w-full max-w-2xl overflow-y-auto rounded-t-2xl border border-border-soft bg-card p-6 shadow-2xl sm:rounded-2xl"
            >
              <div className="mb-5 flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <Avatar name={selected.name} size="lg" />
                  <div>
                    <h2 className="text-lg font-bold text-white">{selected.name}</h2>
                    <p className="text-sm text-slate-500">
                      {selected.users} users · <span className="capitalize">{selected.plan}</span> plan
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedOrg(null)}
                  className="rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-card-soft hover:text-white cursor-pointer"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <p className="mb-3 text-sm text-slate-400">
                Enable or disable modules for this company. The org admin can further switch them off for their workspace, but cannot enable a module you have disabled here.
              </p>

              {/* Overview is always on — it backs the main dashboard. */}
              <div className="mb-2 flex items-center gap-3 rounded-xl border border-primary/30 bg-primary/10 p-3 opacity-80">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent text-white">
                  <LayoutDashboard className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-bold text-white">Overview</span>
                  <span className="block truncate text-xs text-slate-500">Company-wide overview and quick stats.</span>
                </span>
                <Badge variant="secondary">Always on</Badge>
              </div>

              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {TOGGLEABLE_MODULES.map((m) => {
                  const row = selected.modules.find((r) => r.module_key === m.key);
                  const enabled = row ? row.enabled_by_super_admin !== false : true;
                  const Icon = m.icon;
                  return (
                    <button
                      key={m.key}
                      onClick={() => toggleSuperAdminModule(selected.id, m.key, !enabled)}
                      className={cn(
                        "flex items-center gap-3 rounded-xl border p-3 text-left transition-all cursor-pointer",
                        enabled
                          ? "border-primary/30 bg-primary/10 hover:border-primary/60"
                          : "border-border-soft bg-card-soft/40 opacity-70 hover:opacity-100"
                      )}
                    >
                      <span className={cn(
                        "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
                        enabled ? "bg-gradient-to-br from-primary to-accent text-white" : "bg-card-soft text-slate-500"
                      )}>
                        <Icon className="h-4 w-4" />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-bold text-white">{m.name}</span>
                        <span className="block truncate text-xs text-slate-500">{m.description}</span>
                      </span>
                      <span
                        className={cn(
                          "relative h-5 w-9 shrink-0 rounded-full transition-colors",
                          enabled ? "bg-gradient-to-r from-primary to-accent" : "bg-card-soft"
                        )}
                      >
                        <span
                          className={cn(
                            "absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all",
                            enabled ? "left-4.5" : "left-0.5"
                          )}
                        />
                      </span>
                    </button>
                  );
                })}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
