"use client";

import { motion } from "framer-motion";
import { ArrowUpRight, Bot, CheckCircle2, Cpu } from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { Badge, StatusDot } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { hashString } from "@/lib/utils";
import type { AIEmployee } from "@/lib/api/types";

const ROLE_ICONS: Record<string, React.ReactNode> = {
  "Sales": <ArrowUpRight className="h-4 w-4" />,
  "Support": <CheckCircle2 className="h-4 w-4" />,
  "Finance": <Cpu className="h-4 w-4" />,
};

export function EmployeeCard({ employee, index = 0 }: { employee: AIEmployee; index?: number }) {
  const roleKey = employee.role.split(" ")[0] ?? "AI";
  const efficiency = 82 + (hashString(employee.id) % 17); // 82-98%
  const today = 6 + (hashString(employee.id) % 14); // 6-19 tasks

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.06, duration: 0.4 }}
      whileHover={{ y: -6 }}
      className="gradient-border group cursor-pointer rounded-2xl p-[1px]"
    >
      <div className="relative overflow-hidden rounded-2xl bg-card p-6 transition-colors group-hover:bg-card-soft/60">
        <div className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-gradient-to-br from-primary to-accent opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-25" />

        <div className="flex items-start justify-between">
          <div className="relative">
            <Avatar name={employee.name} size="lg" />
            <span className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-card border border-border-soft">
              {ROLE_ICONS[roleKey] ?? <Bot className="h-3 w-3 text-primary-soft" />}
            </span>
          </div>
          <Badge variant={employee.active === false ? "secondary" : "success"}>
            <StatusDot color={employee.active === false ? "#64748b" : "#22c55e"} />
            {employee.active === false ? "Offline" : "Online"}
          </Badge>
        </div>

        <h3 className="mt-4 text-lg font-bold tracking-tight text-white">{employee.name}</h3>
        <p className="text-sm font-semibold text-primary-soft">{employee.role}</p>
        <p className="mt-2 line-clamp-2 text-sm text-slate-400">{employee.description ?? "No description yet"}</p>

        <div className="mt-5 space-y-3">
          <div>
            <div className="mb-1 flex items-center justify-between text-xs font-semibold">
              <span className="text-slate-500">Today&apos;s tasks</span>
              <span className="text-white">{today}</span>
            </div>
            <Progress value={(today / 20) * 100} />
          </div>
          <div>
            <div className="mb-1 flex items-center justify-between text-xs font-semibold">
              <span className="text-slate-500">Efficiency</span>
              <span className="text-gradient">{efficiency}%</span>
            </div>
            <Progress value={efficiency} barClassName="from-accent to-primary" />
          </div>
        </div>

        <div className="mt-5 flex items-center justify-between border-t border-border-soft pt-4">
          <span className="inline-flex items-center gap-1.5 text-xs text-slate-500">
            <Cpu className="h-3.5 w-3.5" /> {employee.model ?? "gpt-5"}
          </span>
          <span className="inline-flex items-center gap-1 text-sm font-bold text-primary-soft transition-transform group-hover:translate-x-1">
            Open <ArrowUpRight className="h-4 w-4" />
          </span>
        </div>
      </div>
    </motion.div>
  );
}
