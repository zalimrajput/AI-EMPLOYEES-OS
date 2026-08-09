"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, Loader2, Sparkles, User, Mail, Lock, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PENDING_WORKSPACE_KEY, signUp } from "@/hooks/use-session";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { ShieldCheck } from "lucide-react";

const COUNTRIES = ["United States", "United Kingdom", "Germany", "India", "UAE", "Canada", "Australia", "Singapore", "Other"];
const TIMEZONES = ["UTC-08:00 (PST)", "UTC-05:00 (EST)", "UTC+00:00 (GMT)", "UTC+01:00 (CET)", "UTC+05:30 (IST)", "UTC+08:00 (SGT)", "UTC+10:00 (AEST)"];

export function RegisterForm() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [loading, setLoading] = useState(false);
  // Self-service: the person signing up becomes the Company Admin for the new
  // workspace — the platform (super admin) does NOT assign admins.
  const [selfService, setSelfService] = useState(true);
  const [form, setForm] = useState({
    company: "",
    email: "",
    password: "",
    confirm: "",
    fullName: "",
    country: COUNTRIES[0],
    timezone: TIMEZONES[2],
  });

  const passwordStrength = getStrength(form.password);
  const passwordsMatch = form.password === form.confirm;

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleCreateWorkspace() {
    if (form.password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    if (!passwordsMatch) {
      toast.error("Passwords do not match");
      return;
    }
    if (!selfService) {
      toast.error("Self-service admin is required — you'll be the Company Admin for your workspace.");
      return;
    }
    setLoading(true);
    try {
      // The workspace the signup is creating. When email confirmation blocks
      // the session, this payload is stored and the org is created on first
      // sign-in (login-form finishes the pending workspace).
      const slug = form.company
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "") || `workspace-${Date.now().toString(36)}`;
      const workspace = {
        name: form.company,
        slug,
        country: form.country,
        industry: "Technology",
      };

      // 1. Create the Supabase Auth user (public).
      const res = await signUp(form.email, form.password, form.fullName);

      // If email confirmation is enabled (Supabase default), there is no
      // session yet — the user must verify their inbox before signing in.
      if (!res.session) {
        localStorage.setItem(PENDING_WORKSPACE_KEY, JSON.stringify(workspace));
        toast.success("Account created! Verify your email, then sign in to create your workspace.");
        router.push("/login");
        return;
      }

      // 2. Create the workspace via the protected FastAPI endpoint with the
      //    fresh session token — the backend assigns creator + membership.
      await api.createOrganization(workspace);
      localStorage.removeItem(PENDING_WORKSPACE_KEY);
      toast.success("Workspace created! Welcome aboard 🎉");
      router.push("/dashboard");
    } catch (err) {
      toast.error((err as Error).message || "Sign up failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {[1, 2].map((s) => (
          <div
            key={s}
            className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${step >= s ? "bg-gradient-to-r from-primary to-accent" : "bg-card-soft"}`}
          />
        ))}
      </div>

      {step === 1 ? (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="company">Company Name</Label>
            <div className="relative">
              <Building2 className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <Input id="company" placeholder="Acme Inc." className="pl-10" value={form.company} onChange={(e) => set("company", e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <select
                id="country"
                value={form.country}
                onChange={(e) => set("country", e.target.value)}
                className="h-11 w-full rounded-xl border border-border-soft bg-card-soft/60 px-3 text-sm text-white focus:border-primary/60 focus:ring-2 focus:ring-primary/25 focus:outline-none"
              >
                {COUNTRIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="timezone">Timezone</Label>
              <select
                id="timezone"
                value={form.timezone}
                onChange={(e) => set("timezone", e.target.value)}
                className="h-11 w-full rounded-xl border border-border-soft bg-card-soft/60 px-3 text-sm text-white focus:border-primary/60 focus:ring-2 focus:ring-primary/25 focus:outline-none"
              >
                {TIMEZONES.map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <motion.div whileTap={{ scale: 0.98 }}>
            <Button type="button" size="lg" className="w-full" onClick={() => setStep(2)}>
              Continue <ArrowRight className="h-4 w-4" />
            </Button>
          </motion.div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="fullName">Full Name</Label>
            <div className="relative">
              <User className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <Input id="fullName" placeholder="Jane Doe" className="pl-10" value={form.fullName} onChange={(e) => set("fullName", e.target.value)} />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <Input id="email" type="email" required placeholder="you@company.com" className="pl-10" value={form.email} onChange={(e) => set("email", e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <Input id="password" type="password" required placeholder="Min 8 characters" className="pl-10" value={form.password} onChange={(e) => set("password", e.target.value)} />
              </div>
              {form.password.length > 0 && (
                <div className="flex items-center gap-2">
                  <div className="h-1 flex-1 overflow-hidden rounded-full bg-card-soft">
                    <motion.div
                      className={`h-full rounded-full transition-all ${strengthColor(passwordStrength)}`}
                      animate={{ width: `${strengthWidth(passwordStrength)}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
                    {["Weak", "Fair", "Good", "Strong"][passwordStrength]}
                  </span>
                </div>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm">Confirm Password</Label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <Input id="confirm" type="password" required placeholder="Repeat password" className="pl-10" value={form.confirm} onChange={(e) => set("confirm", e.target.value)} />
              </div>
              {form.confirm.length > 0 && (
                <p className={`text-[10px] font-bold uppercase tracking-wide ${passwordsMatch ? "text-success" : "text-danger"}`}>
                  {passwordsMatch ? "✓ Match" : "✗ Does not match"}
                </p>
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={() => setSelfService((s) => !s)}
            className="flex w-full items-center gap-3 rounded-xl border border-primary/30 bg-primary/10 px-4 py-3 text-left transition-colors hover:border-primary/50 cursor-pointer"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent text-white">
              <ShieldCheck className="h-4 w-4" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-bold text-white">Self-service admin</span>
              <span className="block text-xs text-slate-500">You&apos;ll be the Company Admin for {form.company || "your workspace"} — full control over members, modules, and the AI workforce.</span>
            </span>
            <span
              className={`relative h-5 w-9 shrink-0 rounded-full transition-colors ${selfService ? "bg-gradient-to-r from-primary to-accent" : "bg-card-soft"}`}
            >
              <span
                className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${selfService ? "left-4.5" : "left-0.5"}`}
              />
            </span>
          </button>

          <motion.div whileTap={{ scale: 0.98 }}>
            <Button type="button" size="lg" className="w-full" disabled={loading} onClick={handleCreateWorkspace}>
              {loading ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Creating workspace…</>
              ) : (
                <><Sparkles className="h-4 w-4" /> Create Workspace</>
              )}
            </Button>
          </motion.div>

          <button
            type="button"
            onClick={() => setStep(1)}
            className="w-full text-center text-sm font-semibold text-slate-500 hover:text-white transition-colors cursor-pointer"
          >
            ← Back
          </button>
        </div>
      )}
    </div>
  );
}

function getStrength(pw: string): number {
  let s = 0;
  if (pw.length >= 8) s++;
  if (pw.length >= 12) s++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
  if (/\d/.test(pw) && /[^A-Za-z0-9]/.test(pw)) s++;
  return Math.min(3, s);
}
function strengthColor(s: number) {
  return ["bg-danger", "bg-warning", "bg-accent", "bg-success"][s];
}
function strengthWidth(s: number) {
  return [20, 45, 70, 100][s];
}
