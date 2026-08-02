"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown } from "lucide-react";

export function StatCard({
  label,
  value,
  delta,
  icon,
  gradient = "from-primary to-secondary",
  loading,
}: {
  label: string;
  value: string;
  delta?: number;
  icon: React.ReactNode;
  gradient?: string;
  loading?: boolean;
}) {
  const positive = (delta ?? 0) >= 0;

  return (
    <motion.div
      whileHover={{ y: -6 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="gradient-border group rounded-2xl p-[1px]"
    >
      <div className="relative overflow-hidden rounded-2xl bg-card p-5">
        <div
          className={cn(
            "pointer-events-none absolute -right-8 -top-8 h-28 w-28 rounded-full bg-gradient-to-br opacity-10 blur-2xl transition-opacity group-hover:opacity-25",
            gradient
          )}
        />
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</p>
            {loading ? (
              <div className="mt-2 h-8 w-20 skeleton rounded-lg" />
            ) : (
              <p className="mt-1.5 text-2xl font-bold tracking-tight text-white">{value}</p>
            )}
          </div>
          <div className={cn("flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-lg", gradient)}>
            {icon}
          </div>
        </div>

        {delta !== undefined && (
          <div className="mt-3 flex items-center gap-1.5 text-xs font-semibold">
            <span
              className={cn(
                "inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5",
                positive ? "bg-success/15 text-green-400" : "bg-danger/15 text-red-400"
              )}
            >
              {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {positive ? "+" : ""}{delta}%
            </span>
            <span className="text-slate-500">vs last month</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
