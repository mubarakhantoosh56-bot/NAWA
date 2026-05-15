import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default [
  {
    ignores: [".next/**", "node_modules/**", "next-env.d.ts", "postcss.config.js"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      globals: {
        React: "readonly",
        RequestInit: "readonly",
        HeadersInit: "readonly",
        Headers: "readonly",
        fetch: "readonly",
        process: "readonly",
        window: "readonly",
      },
    },
    rules: {
      "@typescript-eslint/no-empty-object-type": "off",
    },
  },
];
