import { LoginForm } from "@/components/auth/login-form";
import { Logo } from "@/components/shared/logo";
import { Bot, MailCheck, Quote, Sparkles } from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  return (
    <div className="dark flex min-h-screen bg-background">
      {/* Left — AI illustration */}
      <div className="relative hidden flex-1 overflow-hidden lg:block">
        <div className="absolute inset-0 bg-mesh" />
        <div className="absolute inset-0 bg-grid" />
        <div className="relative flex h-full flex-col justify-between p-12">
          <Link href="/">
            <Logo />
          </Link>

          <div className="space-y-8">
            <div className="glass relative z-10 mx-auto max-w-md rounded-2xl p-6 shadow-2xl shadow-primary/20">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-secondary">
                  <Bot className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">Marketing GPT</p>
                  <p className="text-xs text-slate-400 flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-success" /> Working on Q3 campaign
                  </p>
                </div>
              </div>
              <div className="mt-5 space-y-3">
                <div className="rounded-xl bg-card-soft/70 p-3 text-sm text-slate-300">
                  Drafted 3 email variants for the launch 🚀
                </div>
                <div className="ml-6 rounded-xl bg-gradient-to-r from-primary/30 to-secondary/30 border border-primary/30 p-3 text-sm text-white">
                  Sent quotation to Acme Corp — 25 laptops, PDF attached. ✓
                </div>
              </div>
            </div>

            <div className="glass z-10 mx-auto flex max-w-md items-center gap-4 rounded-2xl p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent/20 text-accent">
                <MailCheck className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-bold text-white">AI handled 48 tasks today</p>
                <p className="text-xs text-slate-400">Emails, CRM, invoices, meetings — zero manual work.</p>
              </div>
            </div>
          </div>

          <p className="text-xs text-slate-500 flex items-center gap-1.5">
            <Quote className="h-3.5 w-3.5" /> “Our AI workforce saves us 30+ hours a week.”
            <Sparkles className="h-3.5 w-3.5 text-accent" />
          </p>
        </div>
      </div>

      {/* Right — login card */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <Link href="/"><Logo /></Link>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Welcome back</h1>
          <p className="mt-2 text-sm text-slate-400">
            Sign in to command your AI workforce.
          </p>
          <div className="mt-8 rounded-2xl border border-border-soft bg-card p-7 shadow-2xl shadow-black/30">
            <LoginForm />
          </div>
        </div>
      </div>
    </div>
  );
}
