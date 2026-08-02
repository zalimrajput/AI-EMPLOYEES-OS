import { cn } from "@/lib/utils";
import { forwardRef } from "react";

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "flex min-h-[96px] w-full rounded-xl border border-border-soft bg-card-soft/60 px-4 py-3 text-sm text-white placeholder:text-slate-500 transition-all duration-200 focus:border-primary/60 focus:bg-card focus:ring-2 focus:ring-primary/25 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50",
      className
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
