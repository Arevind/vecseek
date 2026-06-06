"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function Dialog({
  open,
  onOpenChange,
  trigger,
  title,
  description,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  trigger: ReactNode;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Trigger asChild>{trigger}</DialogPrimitive.Trigger>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-40 bg-slate-950/35 backdrop-blur-sm" />
        <DialogPrimitive.Content
          className={cn(
            "panel-surface fixed left-1/2 top-1/2 z-50 w-[92vw] max-w-xl -translate-x-1/2 -translate-y-1/2 rounded-[30px] p-7",
          )}
        >
          <div className="mb-4 flex items-start justify-between">
            <div>
              <DialogPrimitive.Title className="font-display text-[2rem] leading-none text-text">{title}</DialogPrimitive.Title>
              <DialogPrimitive.Description className="mt-2 text-sm leading-6 text-muted">
                {description}
              </DialogPrimitive.Description>
            </div>
            <DialogPrimitive.Close className="rounded-full border border-black/[0.06] p-2 text-muted transition hover:bg-card-secondary/70 hover:text-text dark:border-white/10">
              <X className="h-4 w-4" />
            </DialogPrimitive.Close>
          </div>
          {children}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
