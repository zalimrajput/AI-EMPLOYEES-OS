"use client";

import { motion } from "framer-motion";
import { ArrowDown, CheckCircle2, CreditCard, Mail, MessageSquare, Users, CalendarClock, FileText } from "lucide-react";

const STEPS = [
  { icon: CreditCard, label: "Customer pays invoice", color: "from-success to-accent" },
  { icon: FileText, label: "Generate receipt", color: "from-primary to-secondary" },
  { icon: Users, label: "Update CRM", color: "from-secondary to-accent" },
  { icon: MessageSquare, label: "Notify sales team", color: "from-accent to-primary" },
  { icon: Mail, label: "Send thank-you email", color: "from-primary to-secondary" },
  { icon: CalendarClock, label: "Schedule follow-up", color: "from-accent to-success" },
];

export function WorkflowDemo() {
  return (
    <section className="relative py-24">
      <div className="absolute inset-0 bg-mesh opacity-60" />
      <div className="relative mx-auto max-w-5xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-bold uppercase tracking-widest text-primary-soft">Automation</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-white md:text-5xl">
            The invoice example,
            <br />
            <span className="text-gradient">fully automated</span>
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            When a customer pays, your entire team springs into action — hands-free.
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 items-center gap-3 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <div key={i} className="relative">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.12 }}
                whileHover={{ y: -4 }}
                className="flex items-center gap-3 rounded-2xl border border-border-soft bg-card/80 p-4 backdrop-blur-xl"
              >
                <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${s.color}`}>
                  <s.icon className="h-5 w-5 text-white" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-bold text-white">{s.label}</p>
                  <p className="text-[11px] text-slate-500 flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3 text-success" /> Automated
                  </p>
                </div>
              </motion.div>
              {i < STEPS.length - 1 && (
                <ArrowDown className="absolute -bottom-4 left-1/2 z-10 h-4 w-4 -translate-x-1/2 text-primary-soft animate-bounce md:hidden" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
