import { RegisterForm } from "@/components/auth/register-form";
import { Logo } from "@/components/shared/logo";
import Link from "next/link";

export default function RegisterPage() {
  return (
    <div className="dark relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-6 py-12">
      <div className="absolute inset-0 bg-mesh" />
      <div className="absolute inset-0 bg-grid" />

      <div className="relative z-10 w-full max-w-lg">
        <div className="mb-8 flex justify-center">
          <Link href="/"><Logo /></Link>
        </div>

        <div className="rounded-2xl border border-border-soft bg-card p-8 shadow-2xl shadow-black/40">
          <h1 className="text-2xl font-bold tracking-tight text-white">Create your workspace</h1>
          <p className="mt-1.5 text-sm text-slate-400">
            Set up your company and deploy your first AI employees in minutes.
          </p>
          <div className="mt-7">
            <RegisterForm />
          </div>
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link href="/login" className="font-bold text-primary-soft hover:text-white transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
