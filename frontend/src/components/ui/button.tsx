import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold tracking-wide transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] cursor-pointer",
  {
    variants: {
      variant: {
        default: "btn-gradient text-white shadow-lg shadow-primary/20",
        secondary:
          "bg-card-soft text-slate-100 border border-border-soft hover:border-primary/40 hover:bg-card hover:text-white shadow-sm",
        ghost: "text-slate-300 hover:bg-card-soft hover:text-white",
        outline:
          "border border-border-soft bg-transparent text-slate-200 hover:border-primary/50 hover:text-white",
        danger:
          "bg-danger/10 text-danger border border-danger/30 hover:bg-danger/20",
        success:
          "bg-success/10 text-success border border-success/30 hover:bg-success/20",
        glass: "glass text-white hover:bg-white/10",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-7 text-base",
        icon: "h-10 w-10 p-0",
        iconSm: "h-8 w-8 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  )
);
Button.displayName = "Button";

export { buttonVariants };
