import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "w-full rounded-2xl border border-black/[0.06] bg-card px-4 py-3 text-sm text-text outline-none transition placeholder:text-muted focus:border-accent/60 focus:ring-2 focus:ring-accent/15 dark:border-white/10",
        className,
      )}
      {...props}
    />
  ),
);

Input.displayName = "Input";
