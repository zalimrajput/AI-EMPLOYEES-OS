"use client";

import { cn, hashString } from "@/lib/utils";

const GRADIENTS = [
  "linear-gradient(135deg,#4f46e5,#06b6d4)",
  "linear-gradient(135deg,#7c3aed,#4f46e5)",
  "linear-gradient(135deg,#06b6d4,#22c55e)",
  "linear-gradient(135deg,#f59e0b,#ef4444)",
  "linear-gradient(135deg,#6366f1,#a855f7)",
  "linear-gradient(135deg,#0ea5e9,#22d3ee)",
];

export function Avatar({
  name,
  src,
  className,
  size = "md",
}: {
  name?: string | null;
  src?: string | null;
  className?: string;
  size?: "sm" | "md" | "lg" | "xl";
}) {
  const sizes = {
    sm: "h-8 w-8 text-xs",
    md: "h-10 w-10 text-sm",
    lg: "h-14 w-14 text-lg",
    xl: "h-24 w-24 text-3xl",
  };

  const label = (name || "AI").split(/\s+/).slice(0, 2).map((p) => p[0]?.toUpperCase()).join("");
  const bg = GRADIENTS[hashString(name || "ai") % GRADIENTS.length];

  if (src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- remote user avatars (Gravatar/SSO)
      <img
        src={src}
        alt={name || "avatar"}
        className={cn("rounded-full object-cover ring-2 ring-primary/30", sizes[size], className)}
      />
    );
  }

  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full font-bold text-white ring-2 ring-white/10",
        sizes[size],
        className
      )}
      style={{ background: bg }}
      aria-label={name || "avatar"}
    >
      {label}
    </div>
  );
}
