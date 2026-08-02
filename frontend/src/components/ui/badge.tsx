import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide",
  {
    variants: {
      variant: {
        default: "bg-primary/15 text-primary-soft border border-primary/30",
        secondary: "bg-card-soft text-slate-300 border border-border-soft",
        accent: "bg-accent/15 text-cyan-300 border border-accent/30",
        success: "bg-success/15 text-green-400 border border-success/30",
        warning: "bg-warning/15 text-amber-400 border border-warning/30",
        danger: "bg-danger/15 text-red-400 border border-danger/30",
        glass: "glass text-slate-200",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

/** Small dot used for status indicators. */
export function StatusDot({ color = "#22c55e" }: { color?: string }) {
  return (
    <span className="relative flex h-2 w-2">
      <span
        className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60"
        style={{ backgroundColor: color }}
      />
      <span
        className="relative inline-flex h-2 w-2 rounded-full"
        style={{ backgroundColor: color }}
      />
    </span>
  );
}
