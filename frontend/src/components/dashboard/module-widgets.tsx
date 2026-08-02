"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Box, Lock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { modulesForDashboard, isModuleEnabled } from "@/lib/modules";
import { useSession } from "@/hooks/use-session";
import { cn } from "@/lib/utils";

/**
 * Renders the widget cards for every module that powers the given dashboard,
 * but only for modules the organization has enabled (both flags on).
 * `dashboardName` mirrors `modules.dashboard` (e.g. "Company Admin Dashboard").
 * When `dashboardName` is null, shows modules marked as global (notifications).
 */
export function ModuleWidgets({
  dashboardName,
  title = "Modules & widgets",
  description = "What this dashboard shows, powered by the modules your org has enabled.",
  enabledModules,
}: {
  dashboardName: string | null;
  title?: string;
  description?: string;
  /** Override the org's enabled modules (used by the Super Admin org preview). */
  enabledModules?: string[] | undefined | null;
}) {
  const { data: session } = useSession();
  const effectiveModules =
    enabledModules !== undefined
      ? enabledModules
      : session?.user?.enabledModules;

  const modules = useMemo(() => {
    return modulesForDashboard(dashboardName).filter(
      (m) => isModuleEnabled(effectiveModules, m.key)
    );
  }, [dashboardName, effectiveModules]);

  if (modules.length === 0) return null;

  const totalWidgets = modules.reduce((acc, m) => acc + m.widgets.length, 0);

  return (
    <section className="space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">{title}</h2>
          <p className="text-sm text-slate-500">{description}</p>
        </div>
        <Badge variant="secondary" className="shrink-0">
          {modules.length} module{modules.length > 1 ? "s" : ""} · {totalWidgets} widgets
        </Badge>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {modules.map((m, mi) => (
          <motion.div
            key={m.key}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: mi * 0.06 }}
          >
            <Card className="h-full overflow-hidden">
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent text-white">
                      <m.icon className="h-4.5 w-4.5" />
                    </span>
                    <div>
                      <CardTitle className="text-sm">{m.name}</CardTitle>
                      <CardDescription className="text-xs">{m.description}</CardDescription>
                    </div>
                  </div>
                  {m.dashboard === null && (
                    <Badge variant="accent" className="shrink-0">Global</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {m.widgets.length === 0 && (
                    <div className="col-span-full flex items-center gap-2 rounded-lg border border-dashed border-border-soft px-3 py-4 text-xs text-slate-500">
                      <Box className="h-3.5 w-3.5" /> No widgets configured yet
                    </div>
                  )}
                  {m.widgets.map((w, wi) => (
                    <div
                      key={w.key}
                      className="group flex items-start gap-2.5 rounded-lg border border-border-soft bg-card-soft/40 p-2.5 transition-colors hover:border-primary/40"
                    >
                      <w.icon className={cn(
                        "mt-0.5 h-4 w-4 shrink-0 text-primary-soft transition-transform group-hover:scale-110",
                        wi % 3 === 1 && "text-accent",
                        wi % 3 === 2 && "text-success"
                      )} />
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-white">{w.name}</p>
                        <p className="truncate text-[11px] text-slate-500">{w.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {effectiveModules && effectiveModules.length === 0 && (
        <div className="flex items-center gap-2 rounded-xl border border-warning/30 bg-warning/10 px-4 py-3 text-xs text-warning">
          <Lock className="h-3.5 w-3.5 shrink-0" />
          All modules are currently disabled for this workspace — enable some in Settings → Modules.
        </div>
      )}
    </section>
  );
}
