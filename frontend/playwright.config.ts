import { defineConfig, devices } from "@playwright/test";

// M7 Slice 3B Correction Round 2: Playwright owns NO server lifecycle here
// (no `webServer` entry). scripts/e2e_orchestrator.py explicitly starts and
// stops both the production frontend and the backend, waits for both to be
// ready over real HTTP, and only then launches this config's test runner.
// This removes Playwright's own webServer teardown entirely from the
// canonical path - see 3B-F1/3B-F3 for why that ownership was reassigned.
const frontendPort = process.env.E2E_FRONTEND_PORT || "3100";
const baseURL = `http://127.0.0.1:${frontendPort}`;

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
