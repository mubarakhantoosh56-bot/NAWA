import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
        line: "rgb(var(--color-line) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        executive: "rgb(var(--color-executive) / <alpha-value>)",
        command: "rgb(var(--color-command) / <alpha-value>)",
        gold: "rgb(var(--color-gold) / <alpha-value>)",
      },
      boxShadow: {
        panel: "0 12px 32px rgba(8, 15, 32, 0.08)",
        command: "0 20px 60px rgba(8, 15, 32, 0.18)",
      },
    },
  },
  plugins: [],
};

export default config;
