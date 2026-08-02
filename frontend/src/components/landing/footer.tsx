import { Logo } from "@/components/shared/logo";
import Link from "next/link";

const COLUMNS = [
  {
    title: "Product",
    links: ["AI Employees", "AI Chat", "Workflows", "Task Board", "Analytics", "Pricing"],
  },
  {
    title: "Company",
    links: ["About", "Careers", "Blog", "Press", "Contact"],
  },
  {
    title: "Resources",
    links: ["Documentation", "API Reference", "Changelog", "Status", "Security"],
  },
];

export function Footer() {
  return (
    <footer className="relative border-t border-border-soft bg-card/40 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-5">
          <div className="md:col-span-2">
            <Logo />
            <p className="mt-4 max-w-xs text-sm text-slate-400">
              The world&apos;s first AI digital workforce. Emails, quotations, CRM, reports and workflows — handled by specialized AI employees.
            </p>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <p className="text-sm font-bold text-white">{col.title}</p>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((l) => (
                  <li key={l}>
                    <Link href="#" className="text-sm text-slate-400 transition-colors hover:text-primary-soft">
                      {l}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border-soft pt-6 sm:flex-row">
          <p className="text-xs text-slate-500">© {new Date().getFullYear()} AI Employee OS. All rights reserved.</p>
          <div className="flex gap-5 text-xs text-slate-500">
            <Link href="#" className="hover:text-white">Privacy</Link>
            <Link href="#" className="hover:text-white">Terms</Link>
            <Link href="#" className="hover:text-white">Cookies</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
