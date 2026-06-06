import { cn } from "@/lib/utils";

export function Badge({
  children,
  variant = "default",
}: {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger";
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full border px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.22em]",
        variant === "default" && "border-accent/15 bg-[rgb(var(--accent)/0.08)] text-accent",
        variant === "success" && "border-success/15 bg-[rgb(var(--success)/0.08)] text-success",
        variant === "warning" && "border-warning/15 bg-[rgb(var(--warning)/0.08)] text-warning",
        variant === "danger" && "border-danger/15 bg-[rgb(var(--danger)/0.08)] text-danger",
      )}
    >
      {children}
    </span>
  );
}
