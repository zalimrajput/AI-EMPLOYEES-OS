"use client";

import { Bell, Menu, MessageSquare, Search } from "lucide-react";
import { ThemeToggle } from "@/components/shared/theme-toggle";
import { Avatar } from "@/components/ui/avatar";
import { StatusDot } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { signOut, type SessionUser } from "@/hooks/use-session";
import { ROLE_META, primaryRole } from "@/lib/roles";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useState } from "react";

export function Navbar({
  user,
  onMenuClick,
}: {
  user: SessionUser | null;
  onMenuClick?: () => void;
}) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const role = user ? primaryRole(user.roles) : null;

  async function handleSignOut() {
    await signOut();
    toast.success("Signed out");
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border-soft bg-background/70 px-4 backdrop-blur-xl md:px-6">
      <Button variant="ghost" size="iconSm" className="md:hidden" onClick={onMenuClick} aria-label="Menu">
        <Menu className="h-5 w-5" />
      </Button>

      {/* Search */}
      <div className="relative hidden max-w-md flex-1 sm:block">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search tasks, employees, workflows…"
          className="h-10 w-full rounded-xl border border-border-soft bg-card-soft/60 pl-10 pr-4 text-sm text-white placeholder:text-slate-500 transition-all focus:border-primary/60 focus:ring-2 focus:ring-primary/25 focus:outline-none"
        />
        <kbd className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded-md border border-border-soft bg-card px-1.5 py-0.5 text-[10px] font-semibold text-slate-500">
          ⌘K
        </kbd>
      </div>

      <div className="flex-1" />

      <ThemeToggle />

      <Button variant="ghost" size="icon" aria-label="AI Chat" onClick={() => router.push("/dashboard/chat")}>
        <MessageSquare className="h-[18px] w-[18px]" />
      </Button>

      <Button variant="ghost" size="icon" aria-label="Notifications" className="relative">
        <Bell className="h-[18px] w-[18px]" />
        <span className="absolute right-2.5 top-2.5 h-2 w-2 rounded-full bg-danger animate-pulse-glow" />
      </Button>

      <div className="flex items-center gap-2.5 border-l border-border-soft pl-4">
        {user ? (
          <>
            <div className="hidden text-right sm:block">
              <p className="text-sm font-bold leading-tight text-white">{user.name ?? "Admin"}</p>
              {role ? (
                <span
                  title={ROLE_META[role].description}
                  className={`mt-0.5 inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${ROLE_META[role].badgeClass}`}
                >
                  <StatusDot color="#22c55e" /> {ROLE_META[role].label}
                </span>
              ) : (
                <p className="text-xs text-slate-500 flex items-center gap-1.5">
                  <StatusDot color="#22c55e" /> Online
                </p>
              )}
            </div>
            <button onClick={handleSignOut} title="Sign out" className="cursor-pointer">
              <Avatar name={user.name ?? user.email} size="md" />
            </button>
          </>
        ) : (
          <Button size="sm" onClick={() => router.push("/login")}>
            Sign in
          </Button>
        )}
      </div>
    </header>
  );
}
