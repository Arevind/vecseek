"use client";

import { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function HoverHint({
  children,
  hint,
  align = "left",
  className,
}: {
  children: ReactNode;
  hint: string;
  align?: "left" | "center" | "right";
  className?: string;
}) {
  return (
    <div className={cn("group relative inline-flex", className)}>
      {children}
      <div
        className={cn(
          "pointer-events-none absolute top-[calc(100%+0.65rem)] z-30 w-56 rounded-2xl border border-black/[0.06] bg-card px-3 py-2 text-xs leading-5 text-muted opacity-0 shadow-float transition duration-200 delay-700 group-hover:translate-y-0 group-hover:opacity-100 dark:border-white/10",
          align === "left" && "left-0 -translate-y-1",
          align === "center" && "left-1/2 -translate-x-1/2 -translate-y-1",
          align === "right" && "right-0 -translate-y-1",
        )}
      >
        {hint}
      </div>
    </div>
  );
}
