"use client";

import { motion } from "framer-motion";
import { Star } from "lucide-react";
import { Avatar } from "@/components/ui/avatar";

const TESTIMONIALS = [
  {
    quote: "Our AI sales assistant sends quotations and follows up while we sleep. We closed 3 deals it prepared — automatically.",
    name: "Sarah Chen",
    role: "CEO, CloudPeak Systems",
  },
  {
    quote: "The support agent handles 60% of tickets end-to-end. Response time dropped from hours to seconds.",
    name: "Marcus Reid",
    role: "COO, Brightline Logistics",
  },
  {
    quote: "Invoices, reminders, CRM updates — all done by our AI finance bot. It replaced an entire admin hire.",
    name: "Amira Hassan",
    role: "Founder, Nova Labs",
  },
];

export function Testimonials() {
  return (
    <section id="testimonials" className="relative py-24 scroll-mt-20">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-bold uppercase tracking-widest text-primary-soft">Testimonials</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-white md:text-5xl">
            Teams love their <span className="text-gradient">AI employees</span>
          </h2>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3">
          {TESTIMONIALS.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ y: -6 }}
              className="glass rounded-2xl p-7"
            >
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((s) => (
                  <Star key={s} className="h-4 w-4 fill-warning text-warning" />
                ))}
              </div>
              <p className="mt-4 text-sm leading-relaxed text-slate-200">“{t.quote}”</p>
              <div className="mt-6 flex items-center gap-3">
                <Avatar name={t.name} size="md" />
                <div>
                  <p className="text-sm font-bold text-white">{t.name}</p>
                  <p className="text-xs text-slate-400">{t.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
