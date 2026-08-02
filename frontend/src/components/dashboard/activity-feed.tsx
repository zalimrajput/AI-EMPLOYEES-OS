"use client";

import { motion } from "framer-motion";
import { Bot, FileText, Mail, CreditCard, Users, CalendarClock, Workflow } from "lucide-react";
import { timeAgo } from "@/lib/utils";

const ICONS: Record<string, React.ReactNode> = {
  email: <Mail className="h-3.5 w-3.5" />,
  invoice: <CreditCard className="h-3.5 w-3.5" />,
  document: <FileText className="h-3.5 w-3.5" />,
  employee: <Users className="h-3.5 w-3.5" />,
  meeting: <CalendarClock className="h-3.5 w-3.5" />,
  workflow: <Workflow className="h-3.5 w-3.5" />,
};

const ACTIVITIES = [
  { id: 1, type: "email", title: "Sales Assistant sent quotation to Acme Corp", time: "2026-07-31T08:12:00Z", accent: "text-accent bg-accent/15" },
  { id: 2, type: "invoice", title: "Finance Bot marked invoice #1042 as paid", time: "2026-07-31T07:45:00Z", accent: "text-green-400 bg-success/15" },
  { id: 3, type: "meeting", title: "Executive Assistant scheduled standup with 6 attendees", time: "2026-07-31T06:30:00Z", accent: "text-violet-400 bg-secondary/15" },
  { id: 4, type: "workflow", title: "Workflow “Customer pays invoice” completed 3 runs", time: "2026-07-30T22:10:00Z", accent: "text-cyan-400 bg-accent/15" },
  { id: 5, type: "document", title: "Support Hero summarized 4 support tickets", time: "2026-07-30T19:02:00Z", accent: "text-amber-400 bg-warning/15" },
  { id: 6, type: "employee", title: "Marketing GPT published LinkedIn campaign draft", time: "2026-07-30T16:40:00Z", accent: "text-pink-400 bg-danger/15" },
];

export function ActivityFeed() {
  return (
    <div className="space-y-1">
      {ACTIVITIES.map((a, i) => (
        <motion.div
          key={a.id}
          initial={{ opacity: 0, x: -12 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.07 }}
          className="flex items-start gap-3 rounded-xl p-3 transition-colors hover:bg-card-soft/60"
        >
          <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${a.accent}`}>
            {ICONS[a.type]}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-slate-200">{a.title}</p>
            <p className="text-xs text-slate-500">{timeAgo(a.time)}</p>
          </div>
          <Bot className="mt-1 h-3.5 w-3.5 shrink-0 text-slate-600" />
        </motion.div>
      ))}
    </div>
  );
}
