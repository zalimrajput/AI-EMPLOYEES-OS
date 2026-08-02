"use client";

import { useQuery } from "@tanstack/react-query";
import { Bot, Cpu, Gauge, TrendingUp } from "lucide-react";
import { StatCard } from "@/components/dashboard/stat-card";
import { ModuleWidgets } from "@/components/dashboard/module-widgets";
import { RevenueChart, TasksChart, EfficiencyChart, UsageBars } from "@/components/dashboard/charts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchOrgStats } from "@/services/data";
import { formatCompact } from "@/lib/utils";

const USAGE = [
  { name: "Email", value: 342 },
  { name: "Quotations", value: 128 },
  { name: "Invoices", value: 96 },
  { name: "CRM Updates", value: 210 },
  { name: "Meeting Notes", value: 74 },
  { name: "Reports", value: 41 },
];

export default function AnalyticsPage() {
  const { data: stats } = useQuery({ queryKey: ["org-stats"], queryFn: fetchOrgStats });

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold text-primary-soft">Performance intelligence</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-white md:text-3xl">Analytics</h1>
        <p className="mt-1 text-sm text-slate-400">Measure how much work your AI workforce absorbs.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="AI Requests" value={formatCompact(stats?.messages ?? 891)} delta={22} icon={<Cpu className="h-5 w-5" />} gradient="from-primary to-secondary" loading={!stats} />
        <StatCard label="Automation Rate" value="68%" delta={14} icon={<Gauge className="h-5 w-5" />} gradient="from-secondary to-accent" loading={false} />
        <StatCard label="Active Employees" value={formatCompact(stats?.activeEmployees ?? 0)} delta={9} icon={<Bot className="h-5 w-5" />} gradient="from-accent to-primary" loading={!stats} />
        <StatCard label="Projected Savings" value="$4.2k" delta={31} icon={<TrendingUp className="h-5 w-5" />} gradient="from-success to-accent" loading={false} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Revenue growth</CardTitle><CardDescription>Monthly recurring revenue attributed to AI workflows</CardDescription></CardHeader>
          <CardContent><RevenueChart /></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Automation efficiency</CardTitle><CardDescription>Share of work handled by AI</CardDescription></CardHeader>
          <CardContent><EfficiencyChart /></CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Tasks completed</CardTitle><CardDescription>Daily throughput across all employees</CardDescription></CardHeader>
          <CardContent><TasksChart /></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>AI usage by tool</CardTitle><CardDescription>Requests per capability this month</CardDescription></CardHeader>
          <CardContent><UsageBars data={USAGE} /></CardContent>
        </Card>
      </div>

      {/* Module widgets — gated by the org's enabled modules */}
      <ModuleWidgets dashboardName="Reports & Analytics Dashboard" />
    </div>
  );
}
