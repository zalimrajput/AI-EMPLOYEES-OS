"use client";

import { motion } from "framer-motion";
import {
  Bot,
  CalendarClock,
  FileText,
  GitBranch,
  LineChart,
  Mail,
  MessageSquare,
  Phone,
  Users,
} from "lucide-react";

const FEATURES = [
  { icon: Bot, title: "AI Executive Assistant", desc: "Understands natural language, executes multi-step business tasks with context memory.", color: "from-primary to-secondary" },
  { icon: Mail, title: "Email Assistant", desc: "Drafts, replies, summarizes threads, classifies and prioritizes your inbox.", color: "from-secondary to-accent" },
  { icon: MessageSquare, title: "WhatsApp Assistant", desc: "Customer support, order confirmations and invoice sharing in any language.", color: "from-accent to-primary" },
  { icon: Users, title: "Intelligent CRM", desc: "Customer & lead management, sales pipelines, AI summaries and relationship insights.", color: "from-success to-accent" },
  { icon: FileText, title: "Quotation & Invoice Engine", desc: "Branded PDFs, tax, discounts, payment links and automated follow-ups.", color: "from-warning to-danger" },
  { icon: CalendarClock, title: "Meeting Assistant", desc: "Transcription, AI summaries, action items, speaker ID and deadline extraction.", color: "from-primary to-accent" },
  { icon: GitBranch, title: "Workflow Automation", desc: "Chain triggers and actions — payments, receipts, CRM updates, notifications — all automatic.", color: "from-secondary to-primary" },
  { icon: LineChart, title: "AI Reporting", desc: "Sales, expenses, customer analytics and forecasting — explained by AI.", color: "from-accent to-success" },
  { icon: Phone, title: "Voice & OCR", desc: "Understands voice messages, reads documents, and answers from your company knowledge base.", color: "from-danger to-secondary" },
];

export function Features() {
  return (
    <section id="features" className="relative py-24 scroll-mt-20">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-bold uppercase tracking-widest text-primary-soft">Capabilities</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-white md:text-5xl">
            One platform. <span className="text-gradient">An entire team.</span>
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            Stop switching between a dozen tools. Your AI employees operate them all for you.
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06 }}
              whileHover={{ y: -6 }}
              className="group rounded-2xl border border-border-soft bg-card p-6 transition-colors hover:border-primary/40"
            >
              <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${f.color} shadow-lg transition-transform group-hover:scale-110`}>
                <f.icon className="h-5 w-5 text-white" />
              </div>
              <h3 className="mt-5 text-lg font-bold text-white">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
