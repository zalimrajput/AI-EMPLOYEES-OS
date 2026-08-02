"use client";

import { cn } from "@/lib/utils";
import { useState } from "react";

export interface TabItem {
  value: string;
  label: React.ReactNode;
  icon?: React.ReactNode;
}

export function Tabs({
  items,
  defaultValue,
  className,
  onValueChange,
}: {
  items: TabItem[];
  defaultValue?: string;
  className?: string;
  onValueChange?: (value: string) => void;
}) {
  const [active, setActive] = useState(defaultValue ?? items[0]?.value);

  return (
    <div className={cn("inline-flex items-center gap-1 rounded-xl bg-card-soft p-1 border border-border-soft", className)}>
      {items.map((item) => {
        const isActive = item.value === active;
        return (
          <button
            key={item.value}
            onClick={() => {
              setActive(item.value);
              onValueChange?.(item.value);
            }}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-sm font-semibold transition-all duration-200 cursor-pointer",
              isActive
                ? "bg-gradient-to-r from-primary to-secondary text-white shadow-lg shadow-primary/25"
                : "text-slate-400 hover:text-white"
            )}
          >
            {item.icon}
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
