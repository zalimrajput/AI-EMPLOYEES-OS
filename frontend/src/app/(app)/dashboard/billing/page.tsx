"use client";

import { useState } from "react";
import { Check, Crown, Rocket, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { motion } from "framer-motion";

const PLANS = [
  {
    name: "Basic",
    price: 19,
    icon: Zap,
    desc: "For freelancers and solo entrepreneurs.",
    features: ["1 user", "500 AI requests/mo", "Email drafting", "100 invoices & quotations", "Basic CRM & reports", "1 GB storage", "Email support"],
    highlight: false,
  },
  {
    name: "Pro",
    price: 49,
    icon: Rocket,
    desc: "For small businesses and growing teams.",
    features: ["Up to 5 users", "10,000 AI requests/mo", "Advanced CRM", "WhatsApp automation", "Meeting summaries & tasks", "Workflow automation", "20 GB storage", "Priority support"],
    highlight: true,
  },
  {
    name: "Business",
    price: 149,
    icon: Crown,
    desc: "For medium and large organizations.",
    features: ["Unlimited users (fair use)", "Multiple AI employees", "Department permissions", "API access & ERP integrations", "Advanced analytics & audit logs", "SSO", "200 GB storage", "Dedicated account manager"],
    highlight: false,
  },
];

export default function BillingPage() {
  const [selected, setSelected] = useState("Pro");

  return (
    <div className="space-y-8">
      <div className="text-center">
        <p className="text-sm font-semibold text-primary-soft">Simple, transparent pricing</p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-white">Billing & Plans</h1>
        <p className="mx-auto mt-2 max-w-xl text-sm text-slate-400">
          One subscription replaces a dozen software tools and an entire admin team.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {PLANS.map((plan, i) => {
          const Icon = plan.icon;
          const isSelected = selected === plan.name;
          return (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ y: -8 }}
              onClick={() => setSelected(plan.name)}
              className={cn(
                "cursor-pointer rounded-2xl p-[1px] transition-all",
                plan.highlight ? "gradient-border" : "border border-border-soft"
              )}
            >
              <div className={cn("relative rounded-2xl bg-card p-6 h-full", isSelected && "ring-2 ring-primary/50")}>
                {plan.highlight && (
                  <Badge variant="default" className="absolute -top-3 left-1/2 -translate-x-1/2">Most popular</Badge>
                )}
                <div className="flex items-center gap-2.5">
                  <div className={cn("flex h-10 w-10 items-center justify-center rounded-xl", plan.highlight ? "bg-gradient-to-br from-primary to-secondary" : "bg-card-soft")}>
                    <Icon className={cn("h-5 w-5", plan.highlight ? "text-white" : "text-primary-soft")} />
                  </div>
                  <h3 className="text-lg font-bold text-white">{plan.name}</h3>
                </div>
                <p className="mt-2 text-sm text-slate-400">{plan.desc}</p>
                <div className="mt-4 flex items-baseline gap-1">
                  <span className="text-4xl font-bold tracking-tight text-white">${plan.price}</span>
                  <span className="text-sm text-slate-500">/month</span>
                </div>
                <ul className="mt-6 space-y-2.5">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-slate-300">
                      <Check className="h-4 w-4 shrink-0 text-success" /> {f}
                    </li>
                  ))}
                </ul>
                <Button
                  variant={plan.highlight ? "default" : "secondary"}
                  className="mt-6 w-full"
                  onClick={() => toast.info(`${plan.name} plan selected — checkout opens with Stripe.`)}
                >
                  {isSelected ? "Current plan" : `Choose ${plan.name}`}
                </Button>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
