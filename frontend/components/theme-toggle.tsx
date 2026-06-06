"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const stored = window.localStorage.getItem("kb-theme");
    const nextDark = stored !== "light";
    document.documentElement.classList.toggle("dark", nextDark);
    setIsDark(nextDark);
    setMounted(true);
  }, []);

  function toggleTheme() {
    const nextDark = !isDark;
    setIsDark(nextDark);
    document.documentElement.classList.toggle("dark", nextDark);
    window.localStorage.setItem("kb-theme", nextDark ? "dark" : "light");
  }

  return (
    <Button variant="secondary" className="gap-2 rounded-full px-3.5 py-2 text-[13px]" onClick={toggleTheme}>
      {mounted && isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      {mounted && isDark ? "Light Mode" : "Dark Mode"}
    </Button>
  );
}
