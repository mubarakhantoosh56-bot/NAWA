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
        ink: "#111827",
        muted: "#6b7280",
        line: "#d9dde5",
        surface: "#f7f8fa",
        accent: "#2563eb",
      },
      boxShadow: {
        panel: "0 1px 2px rgba(17, 24, 39, 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
