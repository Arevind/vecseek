import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        background: "rgb(var(--background) / <alpha-value>)",
        card: "rgb(var(--card) / <alpha-value>)",
        "card-secondary": "rgb(var(--card-secondary) / <alpha-value>)",
        accent: "rgb(var(--accent) / <alpha-value>)",
        accent2: "rgb(var(--accent2) / <alpha-value>)",
        text: "rgb(var(--text) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        success: "rgb(var(--success) / <alpha-value>)",
        warning: "rgb(var(--warning) / <alpha-value>)",
        danger: "rgb(var(--danger) / <alpha-value>)"
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "ui-serif", "Georgia", "serif"],
      },
      backgroundImage: {
        grid: "radial-gradient(circle at 1px 1px, rgba(122,96,72,0.12) 1px, transparent 0)"
      },
      boxShadow: {
        glow: "0 0 0 1px rgb(var(--shadow-ring) / 0.1), 0 18px 50px rgb(var(--shadow-drop) / 0.08)",
        float: "0 22px 60px rgb(var(--shadow-drop) / 0.12)"
      }
    },
  },
  plugins: [],
};

export default config;
