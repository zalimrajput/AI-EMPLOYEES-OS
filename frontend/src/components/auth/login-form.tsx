"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Mail, Lock, ArrowRight, Loader2, ShieldCheck, Building2, User, Wand2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchUserRoles, signIn } from "@/hooks/use-session";
import { homePathForRoles } from "@/lib/roles";
import { supabase } from "@/lib/supabase/client";
import { toast } from "sonner";
import { motion } from "framer-motion";

/** Demo accounts seeded by backend/scripts/seed_demo_users.py. */
const DEMO_ACCOUNTS = [
  {
    label: "Super Admin",
    description: "All companies & platform",
    email: "superadmin@demo.com",
    password: "SuperAdmin@123",
    icon: ShieldCheck,
    className: "from-danger to-warning",
  },
  {
    label: "Org Admin",
    description: "Own company dashboards",
    email: "orgadmin@demo.com",
    password: "OrgAdmin@123",
    icon: Building2,
    className: "from-primary to-secondary",
  },
  {
    label: "Employee",
    description: "Role-based workspace",
    email: "employee@demo.com",
    password: "Employee@123",
    icon: User,
    className: "from-accent to-success",
  },
];

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  /** Shared: sign in with Supabase, then redirect by the user's role. */
  async function signInAndRedirect(email: string, password: string, successMessage: string) {
    setLoading(true);
    try {
      await signIn(email, password);

      // Role-based redirect: Owners/Admins land on the dashboard, Employees on
      // their tasks. A user without roles yet (e.g. before workspace setup)
      // goes to the dashboard to finish onboarding.
      const {
        data: { session },
      } = await supabase.auth.getSession();
      const roles = session ? await fetchUserRoles(session.user.id) : [];

      toast.success(successMessage);
      router.push(homePathForRoles(roles));
    } catch (err) {
      toast.error((err as Error).message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await signInAndRedirect(email, password, "Welcome back!");
  }

  /** One-click demo login: fill the fields and sign in as that role. */
  async function handleDemoLogin(email: string, password: string) {
    setEmail(email);
    setPassword(password);
    await signInAndRedirect(email, password, `Signed in as ${email}`);
  }

  async function handleOAuth(provider: "google" | "azure") {
    toast.info("Redirecting to sign-in…");
    // Supabase OAuth flows are wired via the Supabase project; the URL is
    // configured there (https://supabase.com/dashboard -> Auth -> URL Configuration).
    const { error } = await supabase.auth.signInWithOAuth({ provider });
    if (error) toast.error(error.message);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Demo logins — one-click role selector */}
      <div className="rounded-xl border border-primary/20 bg-primary/5 p-3">
        <p className="mb-2 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-primary-soft">
          <Wand2 className="h-3.5 w-3.5" /> Try a demo role
        </p>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          {DEMO_ACCOUNTS.map((a) => {
            const Icon = a.icon;
            return (
              <motion.button
                key={a.email}
                type="button"
                whileTap={{ scale: 0.97 }}
                disabled={loading}
                onClick={() => handleDemoLogin(a.email, a.password)}
                className="flex items-center gap-2 rounded-lg border border-border-soft bg-card px-2.5 py-2 text-left transition-all hover:border-primary/50 hover:bg-card-soft cursor-pointer disabled:opacity-60"
              >
                <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-gradient-to-br ${a.className} text-white`}>
                  <Icon className="h-3.5 w-3.5" />
                </span>
                <span className="min-w-0">
                  <span className="block text-xs font-bold text-white">{a.label}</span>
                  <span className="block truncate text-[10px] text-slate-500">{a.description}</span>
                </span>
              </motion.button>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Button type="button" variant="secondary" onClick={() => handleOAuth("google")}>
          <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.27-4.74 3.27-8.1z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.1A6.6 6.6 0 0 1 5.5 12c0-.73.13-1.44.34-2.1V7.06H2.18a11 11 0 0 0 0 9.88l3.66-2.84z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15A11 11 0 0 0 2.18 7.06L5.84 9.9C6.71 7.31 9.14 5.38 12 5.38z" />
          </svg>
          Google
        </Button>
        <Button type="button" variant="secondary" onClick={() => handleOAuth("azure")}>
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
            <rect x="2" y="2" width="9.5" height="9.5" fill="#f25022" />
            <rect x="12.5" y="2" width="9.5" height="9.5" fill="#7fba00" />
            <rect x="2" y="12.5" width="9.5" height="9.5" fill="#00a4ef" />
            <rect x="12.5" y="12.5" width="9.5" height="9.5" fill="#ffb900" />
          </svg>
          Microsoft
        </Button>
      </div>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border-soft" />
        </div>
        <div className="relative flex justify-center">
          <span className="bg-card px-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
            or continue with email
          </span>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <div className="relative">
          <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <Input
            id="email"
            type="email"
            required
            placeholder="you@company.com"
            className="pl-10"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="password">Password</Label>
          <button type="button" className="text-xs font-semibold text-primary-soft hover:text-white transition-colors cursor-pointer">
            Forgot password?
          </button>
        </div>
        <div className="relative">
          <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <Input
            id="password"
            type="password"
            required
            placeholder="••••••••"
            className="pl-10"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
      </div>

      <motion.div whileTap={{ scale: 0.98 }}>
        <Button type="submit" className="w-full" size="lg" disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Sign in <ArrowRight className="h-4 w-4" /></>}
        </Button>
      </motion.div>

      <p className="text-center text-sm text-slate-500">
        Don&apos;t have an account?{" "}
        <button
          type="button"
          onClick={() => router.push("/register")}
          className="font-bold text-primary-soft hover:text-white transition-colors cursor-pointer"
        >
          Create workspace
        </button>
      </p>
    </form>
  );
}
