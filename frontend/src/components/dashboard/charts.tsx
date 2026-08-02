"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const TOOLTIP_STYLE = {
  background: "#111827",
  border: "1px solid #263042",
  borderRadius: "12px",
  fontSize: "12px",
  color: "#e5e7eb",
};

export const REVENUE_DATA = [
  { month: "Jan", revenue: 4200, ai: 1800 },
  { month: "Feb", revenue: 5600, ai: 2400 },
  { month: "Mar", revenue: 6100, ai: 2900 },
  { month: "Apr", revenue: 7400, ai: 3600 },
  { month: "May", revenue: 8200, ai: 4100 },
  { month: "Jun", revenue: 9600, ai: 5200 },
  { month: "Jul", revenue: 11200, ai: 6400 },
];

export const TASKS_DATA = [
  { day: "Mon", tasks: 14 },
  { day: "Tue", tasks: 22 },
  { day: "Wed", tasks: 18 },
  { day: "Thu", tasks: 27 },
  { day: "Fri", tasks: 24 },
  { day: "Sat", tasks: 9 },
  { day: "Sun", tasks: 6 },
];

export const EFFICIENCY_DATA = [
  { name: "Automated", value: 68 },
  { name: "Manual", value: 24 },
  { name: "Pending", value: 8 },
];

const PIE_COLORS = ["#4f46e5", "#06b6d4", "#7c3aed"];

export function RevenueChart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={REVENUE_DATA} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4f46e5" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#4f46e5" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="ai" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#06b6d4" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#263042" vertical={false} />
        <XAxis dataKey="month" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
        <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
        <Tooltip contentStyle={TOOLTIP_STYLE} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area type="monotone" dataKey="revenue" stroke="#4f46e5" strokeWidth={2.5} fill="url(#rev)" name="Revenue ($)" />
        <Area type="monotone" dataKey="ai" stroke="#06b6d4" strokeWidth={2.5} fill="url(#ai)" name="AI-handled ($)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function TasksChart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={TASKS_DATA} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="bars" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#7c3aed" />
            <stop offset="100%" stopColor="#4f46e5" />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#263042" vertical={false} />
        <XAxis dataKey="day" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
        <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
        <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "rgba(79,70,229,0.08)" }} />
        <Bar dataKey="tasks" fill="url(#bars)" radius={[8, 8, 0, 0]} name="Tasks" />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function EfficiencyChart() {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={EFFICIENCY_DATA}
          dataKey="value"
          nameKey="name"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={4}
          strokeWidth={0}
        >
          {EFFICIENCY_DATA.map((_, i) => (
            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip contentStyle={TOOLTIP_STYLE} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function UsageBars({ data }: { data: { name: string; value: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#263042" horizontal={false} />
        <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
        <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} width={90} />
        <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "rgba(6,182,212,0.08)" }} />
        <Bar dataKey="value" fill="#06b6d4" radius={[0, 8, 8, 0]} name="Requests" />
      </BarChart>
    </ResponsiveContainer>
  );
}
