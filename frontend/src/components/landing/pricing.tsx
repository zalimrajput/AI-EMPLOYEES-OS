"use client";

import { motion } from "framer-motion";
import { Check, Crown, Rocket, Zap } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const PLANS = [
  {
    name: "Basic",
    price: 19,
    icon: Zap,
    desc: "For freelancers and solo entrepreneurs.",
    features: ["1 user", "500 AI requests/mo", "Email drafting", "Basic WhatsApp replies", "100 invoices & quotations", "1 GB storage"],
  },
  {
    name: "Pro",
    price: 49,
    icon: Rocket,
    desc: "For small businesses and growing teams.",
    features: ["Up to 5 users", "10,000 AI requests/mo", "Advanced CRM", "WhatsApp automation", "Meeting summaries & tasks", "Workflow automation", "20 GB storage"],
    popular: true,
  },
  {
    name: "Business",
    price: 149,
    icon: Crown,
    desc: "For medium and large organizations.",
    features: ["Unlimited users (fair use)", "Multiple AI employees", "Department permissions", "API & ERP integrations", "Advanced analytics + audit logs", "SSO", "200 GB storage"],
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="relative py-24 scroll-mt-20">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-bold uppercase tracking-widest text-primary-soft">Pricing</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-white md:text-5xl">
            Less than one hire. <span className="text-gradient">An entire team.</span>
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            Replace 10 subscriptions and a dozen admin hours with a single AI workforce.
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {PLANS.map((plan, i) => {
            const Icon = plan.icon;
            return (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -8 }}
                className={cn("rounded-2xl p-[1px]", plan.popular ? "gradient-border" : "border border-border-soft")}
              >
                <div className="relative h-full rounded-2xl bg-card p-7">
                  {plan.popular && (
                    <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">Most popular</Badge>
                  )}
                  <div className="flex items-center gap-2.5">
                    <div className={cn("flex h-10 w-10 items-center justify-center rounded-xl", plan.popular ? "bg-gradient-to-br from-primary to-secondary" : "bg-card-soft")}>
                      <Icon className={cn("h-5 w-5", plan.popular ? "text-white" : "text-primary-soft")} />
                    </div>
                    <h3 className="text-lg font-bold text-white">{plan.name}</h3>
                  </div>
                  <div className="mt-4 flex items-baseline gap-1">
                    <span className="text-4xl font-bold text-white">${plan.price}</span>
                    <span className="text-sm text-slate-500">/month</span>
                  </div>
                  <p className="mt-2 text-sm text-slate-400">{plan.desc}</p>
                  <ul className="mt-6 space-y-2.5">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-center gap-2 text-sm text-slate-300">
                        <Check className="h-4 w-4 shrink-0 text-success" /> {f}
                      </li>
                    ))}
                  </ul>
                  <Link href="/register" className="mt-7 block">
                    <Button variant={plan.popular ? "default" : "secondary"} className="w-full">
                      Start with {plan.name}
                    </Button>
                  </Link>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
