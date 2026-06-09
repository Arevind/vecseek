"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Braces,
  FolderKanban,
  SearchCode,
  Settings2,
} from "lucide-react";
import { ReactNode, useEffect, useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { HoverHint } from "@/components/ui/hover-hint";
import { cn } from "@/lib/utils";

const navItems = [
  {
    href: "/",
    label: "Library",
    description: "Browse folders, create new docks, and monitor indexed volume.",
    icon: FolderKanban,
  },
  {
    href: "/#retrieval-lab",
    label: "Retrieval",
    description: "Test live search quality and inspect the exact chunks being returned.",
    icon: SearchCode,
  },
  {
    href: "/settings",
    label: "Settings",
    description: "Adjust default retrieval depth, chunk size, and overlap behavior.",
    icon: Settings2,
  },
  {
    href: "/api-reference",
    label: "API Reference",
    description: "See the request shapes and endpoints used by the product UI.",
    icon: Braces,
  },
];

function VecSeekLogo() {
  return (
    <div className="flex h-[52px] w-[52px] items-center justify-center rounded-[20px] border border-black/5 bg-card shadow-[inset_0_1px_0_rgba(255,255,255,0.42)] dark:border-white/10 dark:bg-card-secondary">
      <svg
        viewBox="0 0 64 64"
        aria-hidden="true"
        className="h-9 w-9"
        fill="none"
      >
        <path
          d="M16 14C16 11.7909 17.7909 10 20 10H35.5L48 22.5V45C48 47.2091 46.2091 49 44 49H20C17.7909 49 16 47.2091 16 45V14Z"
          stroke="rgb(var(--text))"
          strokeOpacity="0.78"
          strokeWidth="2.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M35.5 10V19.5C35.5 21.1569 36.8431 22.5 38.5 22.5H48"
          stroke="rgb(var(--text))"
          strokeOpacity="0.78"
          strokeWidth="2.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path d="M24 19.5H31" stroke="rgb(var(--muted))" strokeWidth="2.5" strokeLinecap="round" />
        <path d="M24 25.5H30" stroke="rgb(var(--muted))" strokeWidth="2.5" strokeLinecap="round" />
        <path d="M27 33L34 29L41 33L41 41L34 45L27 41V33Z" stroke="rgb(var(--muted))" strokeWidth="2.2" strokeLinejoin="round" />
        <path d="M27 33L20 37V45L27 41" stroke="rgb(var(--muted))" strokeWidth="2.2" strokeLinejoin="round" />
        <path d="M34 29L20 37" stroke="rgb(var(--muted))" strokeWidth="2.2" strokeLinecap="round" />
        <path d="M34 45V37" stroke="rgb(var(--muted))" strokeWidth="2.2" strokeLinecap="round" />
        <circle cx="20" cy="37" r="2.2" fill="rgb(var(--text))" fillOpacity="0.84" />
        <circle cx="27" cy="33" r="2.2" fill="rgb(var(--accent))" />
        <circle cx="27" cy="41" r="2.2" fill="rgb(var(--text))" fillOpacity="0.84" />
        <circle cx="34" cy="29" r="2.2" fill="rgb(var(--accent2))" />
        <circle cx="34" cy="37" r="2.2" fill="rgb(var(--accent))" />
        <circle cx="34" cy="45" r="2.2" fill="rgb(var(--accent2))" />
        <circle cx="41" cy="33" r="2.2" fill="rgb(var(--text))" fillOpacity="0.84" />
        <circle
          cx="43"
          cy="43"
          r="9"
          stroke="rgb(var(--accent))"
          strokeWidth="3.2"
        />
        <circle cx="43" cy="43" r="1.8" fill="rgb(var(--accent2))" />
        <path d="M48.8 48.8L53.5 53.5" stroke="rgb(var(--text))" strokeOpacity="0.82" strokeWidth="3.2" strokeLinecap="round" />
        <path d="M43 43L48.2 38.1" stroke="rgb(var(--accent2))" strokeWidth="2.8" strokeLinecap="round" />
        <path d="M46.1 38.1H48.2V40.2" stroke="rgb(var(--accent2))" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [hash, setHash] = useState("");

  useEffect(() => {
    const syncHash = () => setHash(window.location.hash);
    syncHash();
    window.addEventListener("hashchange", syncHash);
    return () => window.removeEventListener("hashchange", syncHash);
  }, []);

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-[1500px] px-4 py-4 sm:px-6 lg:px-8">
        <div className="grid gap-5 lg:grid-cols-[248px,minmax(0,1fr)]">
          <aside className="panel-surface flex h-fit flex-col rounded-[30px] p-4 lg:sticky lg:top-4 lg:min-h-[calc(100vh-2rem)]">
            <div className="flex items-center justify-between gap-4 rounded-[24px] border border-black/5 bg-card-secondary/55 px-4 py-4 dark:border-white/10">
              <div className="min-w-0">
                <p className="font-display text-[1.9rem] leading-none tracking-[0.01em] text-text">VecSeek</p>
                <p className="mt-1 text-xs uppercase tracking-[0.28em] text-muted">Document Operations</p>
              </div>
              <VecSeekLogo />
            </div>

            <nav className="mt-5 hidden space-y-2 lg:block">
              {navItems.map((item) => {
                const isActive =
                  item.href === "/"
                    ? pathname === "/"
                    : item.href.startsWith("/#")
                      ? pathname === "/" && hash === item.href.slice(1)
                      : pathname === item.href;
                const Icon = item.icon;

                return (
                  <HoverHint key={item.href} hint={item.description} align="right" className="flex">
                    <Link
                      href={item.href}
                      className={cn(
                        "flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm transition",
                        isActive
                          ? "bg-text text-white shadow-float dark:bg-card-secondary dark:text-text dark:shadow-none"
                          : "text-muted hover:bg-card-secondary/65 hover:text-text",
                      )}
                    >
                      <Icon className={cn("h-4 w-4", isActive ? "text-white dark:text-text" : "text-accent")} />
                      <span className="font-medium">{item.label}</span>
                    </Link>
                  </HoverHint>
                );
              })}
            </nav>

            <div className="mt-5 flex gap-2 overflow-x-auto pb-1 lg:hidden">
              {navItems.map((item) => {
                const isActive =
                  item.href === "/"
                    ? pathname === "/"
                    : item.href.startsWith("/#")
                      ? pathname === "/" && hash === item.href.slice(1)
                      : pathname === item.href;
                const Icon = item.icon;

                return (
                  <HoverHint key={item.href} hint={item.description} align="center">
                    <Link
                      href={item.href}
                      className={cn(
                        "inline-flex min-w-max items-center gap-2 rounded-full border px-3.5 py-2 text-sm transition",
                        isActive
                          ? "border-text bg-text text-white dark:border-white/10 dark:bg-card-secondary dark:text-text"
                          : "border-black/[0.06] bg-card text-muted hover:text-text dark:border-white/10",
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      {item.label}
                    </Link>
                  </HoverHint>
                );
              })}
            </div>

            <div className="mt-auto hidden rounded-[24px] border border-black/5 bg-card-secondary/45 p-4 lg:block dark:border-white/10">
              <p className="section-label">Flow</p>
              <p className="mt-2 text-sm leading-6 text-muted">
                Upload a source file, index the folder, and validate results before wiring the public API.
              </p>
            </div>
          </aside>

          <main className="min-w-0">
            <div className="mb-4 flex items-center justify-end">
              <ThemeToggle />
            </div>
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
