import { cn } from "@/lib/utils";
import { Sparkles } from "lucide-react";

export function Logo({
  className,
  iconOnly = false,
  size = "md",
}: {
  className?: string;
  iconOnly?: boolean;
  size?: "sm" | "md" | "lg";
}) {
  const iconSizes = { sm: "h-7 w-7", md: "h-9 w-9", lg: "h-12 w-12" };
  const textSizes = { sm: "text-base", md: "text-lg", lg: "text-2xl" };

  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <div
        className={cn(
          "relative flex items-center justify-center rounded-xl bg-gradient-to-br from-primary via-secondary to-accent shadow-lg shadow-primary/30",
          iconSizes[size]
        )}
      >
        <Sparkles className="h-1/2 w-1/2 text-white" strokeWidth={2.5} />
        <div className="absolute inset-0 rounded-xl bg-white/20 animate-pulse-glow" />
      </div>
      {!iconOnly && (
        <span className={cn("font-bold tracking-tight text-white", textSizes[size])}>
          AI<span className="text-gradient"> Employee OS</span>
        </span>
      )}
    </div>
  );
}
