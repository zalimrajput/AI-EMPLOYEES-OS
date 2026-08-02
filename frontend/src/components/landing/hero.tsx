"use client";

import { motion } from "framer-motion";
import { Bot, CheckCircle2, Mail, Play, Sparkles, Zap } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const FLOATERS = [
  { className: "top-8 left-[6%] animate-float", delay: 0 },
  { className: "top-1/3 right-[8%] animate-float-slow", delay: 1.2 },
  { className: "bottom-24 left-[10%] animate-float-slow", delay: 0.6 },
];

export function Hero() {
  return (
    <section className="relative overflow-hidden pb-20 pt-28 md:pt-36">
      <div className="absolute inset-0 bg-mesh" />
      <div className="absolute inset-0 bg-grid" />
      <div className="pointer-events-none absolute left-1/2 top-0 h-[500px] w-[700px] -translate-x-1/2 rounded-full bg-primary/20 blur-[140px]" />

      <div className="relative mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-3xl text-center">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <Badge variant="glass" className="mb-6 px-4 py-1.5">
              <Sparkles className="h-3.5 w-3.5 text-accent" />
              The world&apos;s first AI digital workforce
            </Badge>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl font-bold leading-tight tracking-tight text-white sm:text-6xl md:text-7xl"
          >
            Hire your{" "}
            <span className="text-gradient">AI workforce</span>
            <br />
            and never do busywork again
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mx-auto mt-6 max-w-2xl text-lg text-slate-400"
          >
            AI Employee OS doesn&apos;t just answer questions — it performs. Emails, quotations,
            invoices, CRM, meetings, reports and workflows — handled end-to-end by specialized AI employees.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row"
          >
            <Link href="/register" className="w-full sm:w-auto">
              <Button size="lg" className="w-full sm:w-auto">
                <Zap className="h-4 w-4" /> Start free workspace
              </Button>
            </Link>
            <Link href="/login" className="w-full sm:w-auto">
              <Button size="lg" variant="glass" className="w-full sm:w-auto">
                <Play className="h-4 w-4" /> Watch demo
              </Button>
            </Link>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-6 text-sm text-slate-500"
          >
            No credit card required · 500 AI requests free every month
          </motion.p>
        </div>

        {/* Animated dashboard mockup */}
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="relative mx-auto mt-16 max-w-5xl"
        >
          <div className="gradient-border rounded-2xl p-[1px] shadow-2xl shadow-primary/20">
            <div className="rounded-2xl bg-card/80 p-4 backdrop-blur-xl md:p-6">
              <div className="flex items-center gap-2 border-b border-border-soft pb-3">
                <span className="h-3 w-3 rounded-full bg-danger/80" />
                <span className="h-3 w-3 rounded-full bg-warning/80" />
                <span className="h-3 w-3 rounded-full bg-success/80" />
                <span className="ml-3 text-xs font-semibold text-slate-500">app.aiemployeeos.com — AI Employee OS</span>
              </div>
              <div className="grid grid-cols-3 gap-4 pt-4">
                {[
                  { label: "AI Employees", value: "245", delta: "+18%" },
                  { label: "Tasks Done", value: "1,284", delta: "+12%" },
                  { label: "Revenue", value: "$42.1k", delta: "+31%" },
                ].map((s) => (
                  <div key={s.label} className="rounded-xl bg-card-soft/60 p-3 md:p-4">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 md:text-xs">{s.label}</p>
                    <p className="mt-1 text-base font-bold text-white md:text-2xl">{s.value}</p>
                    <p className="text-[10px] font-bold text-success md:text-xs">{s.delta}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center gap-3 rounded-xl border border-primary/30 bg-primary/10 p-3 md:p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-secondary md:h-10 md:w-10">
                  <Bot className="h-4 w-4 text-white md:h-5 md:w-5" />
                </div>
                <p className="text-xs text-slate-200 md:text-sm">
                  <span className="font-bold text-white">Sales Assistant:</span> Sent quotation to Acme Corp — 25 laptops, PDF attached ✓
                </p>
                <CheckCircle2 className="ml-auto h-4 w-4 shrink-0 text-success md:h-5 md:w-5" />
              </div>
              <div className="mt-3 flex items-center gap-3 rounded-xl border border-accent/30 bg-accent/10 p-3 md:p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent/20 md:h-10 md:w-10">
                  <Mail className="h-4 w-4 text-cyan-300 md:h-5 md:w-5" />
                </div>
                <p className="text-xs text-slate-200 md:text-sm">
                  <span className="font-bold text-white">Marketing GPT:</span> Published Q3 launch campaign to LinkedIn & X
                </p>
                <Zap className="ml-auto h-4 w-4 shrink-0 text-accent md:h-5 md:w-5" />
              </div>
            </div>
          </div>

          {/* Floating chips */}
          {FLOATERS.map((f, i) => (
            <motion.div
              key={i}
              className={`glass absolute hidden rounded-xl px-3 py-2 text-xs font-bold text-white shadow-xl lg:block ${f.className}`}
              style={{ animationDelay: `${f.delay}s` }}
            >
              {i === 0 && "✉️ 3 emails drafted"}
              {i === 1 && "🧾 Invoice #1042 sent"}
              {i === 2 && "📅 Meeting scheduled"}
            </motion.div>
          ))}
        </motion.div>

        {/* Social proof */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-20 flex flex-wrap items-center justify-center gap-x-10 gap-y-4 text-center"
        >
          {["Acme Corp", "GlobalTech", "Nova Labs", "Brightline", "CloudPeak", "Vertex"].map((c) => (
            <span key={c} className="text-sm font-bold uppercase tracking-widest text-slate-600">
              {c}
            </span>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
