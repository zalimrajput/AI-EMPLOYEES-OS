import Link from "next/link";
import { Hero } from "@/components/landing/hero";
import { Features } from "@/components/landing/features";
import { WorkflowDemo } from "@/components/landing/workflow-demo";
import { Pricing } from "@/components/landing/pricing";
import { Testimonials } from "@/components/landing/testimonials";
import { CTA } from "@/components/landing/cta";
import { Footer } from "@/components/landing/footer";
import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";

export default function Home() {
  return (
    <div className="dark min-h-screen bg-background">
      {/* Navbar */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-border-soft/60 bg-background/60 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary via-secondary to-accent shadow-lg shadow-primary/30">
              <span className="text-sm font-bold text-white">✦</span>
            </div>
            <span className="text-sm font-bold tracking-tight text-white">
              AI <span className="text-gradient">Employee OS</span>
            </span>
          </Link>
          <nav className="hidden items-center gap-7 text-sm font-semibold text-slate-400 md:flex">
            <Link href="#features" className="transition-colors hover:text-white">Features</Link>
            <Link href="#pricing" className="transition-colors hover:text-white">Pricing</Link>
            <Link href="#testimonials" className="transition-colors hover:text-white">Customers</Link>
          </nav>
          <div className="hidden items-center gap-3 md:flex">
            <Link href="/login"><Button variant="ghost">Sign in</Button></Link>
            <Link href="/register"><Button size="sm">Get started</Button></Link>
          </div>
          <Button variant="ghost" size="icon" className="md:hidden" aria-label="Menu">
            <Menu className="h-5 w-5" />
          </Button>
        </div>
      </header>

      <Hero />
      <Features />
      <WorkflowDemo />
      <Pricing />
      <Testimonials />
      <CTA />
      <Footer />
    </div>
  );
}
