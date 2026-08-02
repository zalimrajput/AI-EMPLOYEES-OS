"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";

export function CTA() {
  return (
    <section className="relative py-24">
      <div className="mx-auto max-w-5xl px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="gradient-border relative overflow-hidden rounded-3xl p-[1px]"
        >
          <div className="relative overflow-hidden rounded-3xl bg-card px-8 py-16 text-center md:px-16">
            <div className="absolute inset-0 bg-mesh opacity-70" />
            <div className="pointer-events-none absolute left-1/2 top-0 h-64 w-[500px] -translate-x-1/2 rounded-full bg-primary/25 blur-[100px]" />
            <div className="relative">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-secondary shadow-2xl shadow-primary/40">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <h2 className="mt-6 text-3xl font-bold tracking-tight text-white md:text-5xl">
                Ready to hire your <span className="text-gradient">AI workforce?</span>
              </h2>
              <p className="mx-auto mt-4 max-w-xl text-lg text-slate-400">
                Deploy your first AI employee in minutes. Start with 500 free AI requests every month.
              </p>
              <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Link href="/register">
                  <span className="btn-gradient inline-flex h-12 items-center gap-2 rounded-xl px-8 text-base font-semibold text-white shadow-lg shadow-primary/25">
                    Create free workspace <ArrowRight className="h-4 w-4" />
                  </span>
                </Link>
                <Link href="/login">
                  <span className="glass inline-flex h-12 items-center gap-2 rounded-xl px-8 text-base font-semibold text-white">
                    Sign in
                  </span>
                </Link>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
