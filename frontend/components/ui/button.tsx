import * as React from "react";

import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "ghost" | "danger";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-2xl px-4 py-2.5 text-sm font-semibold tracking-[0.01em] transition duration-200 disabled:cursor-not-allowed disabled:opacity-60",
        variant === "default" && "bg-accent2 text-white hover:bg-accent shadow-float dark:bg-accent dark:text-slate-950 dark:hover:opacity-90",
        variant === "secondary" && "border border-black/[0.06] bg-card text-text hover:bg-card-secondary/75 dark:border-white/10",
        variant === "ghost" && "bg-transparent text-muted hover:bg-card-secondary/60 hover:text-text",
        variant === "danger" && "border border-danger/15 bg-[rgb(var(--danger)/0.08)] text-danger hover:bg-danger/15",
        className,
      )}
      {...props}
    />
  ),
);

Button.displayName = "Button";
