import * as React from "react";

import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "min-h-32 w-full rounded-[24px] border border-black/[0.06] bg-card px-4 py-3.5 text-sm leading-7 text-text outline-none transition placeholder:text-muted focus:border-accent/60 focus:ring-2 focus:ring-accent/15 dark:border-white/10",
        className,
      )}
      {...props}
    />
  ),
);

Textarea.displayName = "Textarea";
