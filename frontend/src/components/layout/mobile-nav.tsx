"use client";

import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "@/components/layout/sidebar";
import { Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { ADMIN_ONLY_PATHS, isAdmin } from "@/lib/roles";
import { navForModules } from "@/lib/modules";
import type { SessionUser } from "@/hooks/use-session";

export function MobileBottomNav({ user }: { user: SessionUser | null }) {
  const pathname = usePathname();
  const admin = isAdmin(user?.roles);
  // Hide admin-only sections from staff, matching the sidebar, and drop
  // nav items whose module is disabled for the org.
  const visibleItems = navForModules(
    NAV_ITEMS.filter(
      ({ href }) => admin || !ADMIN_ONLY_PATHS.some((path) => href.startsWith(path))
    ),
    user?.enabledModules
  );
  const items = [...visibleItems.slice(0, 4)];

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex h-16 items-center justify-around border-t border-border-soft bg-card/90 backdrop-blur-xl md:hidden">
      {items.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || pathname.startsWith(href);
        return (
          <Link key={href} href={href} className="relative flex flex-col items-center gap-1 px-3 py-1.5">
            {active && (
              <motion.span
                layoutId="mobile-active"
                className="absolute -top-2 h-1 w-8 rounded-full bg-gradient-to-r from-primary to-accent"
              />
            )}
            <Icon className={cn("h-5 w-5", active ? "text-primary-soft" : "text-slate-500")} />
            <span className={cn("text-[10px] font-semibold", active ? "text-white" : "text-slate-500")}>
              {label.split(" ")[0]}
            </span>
          </Link>
        );
      })}
      <Link href="/dashboard/settings" className="flex flex-col items-center gap-1 px-3 py-1.5">
        <Settings className={cn("h-5 w-5", pathname.startsWith("/dashboard/settings") ? "text-primary-soft" : "text-slate-500")} />
        <span className="text-[10px] font-semibold text-slate-500">Settings</span>
      </Link>
    </nav>
  );
}
