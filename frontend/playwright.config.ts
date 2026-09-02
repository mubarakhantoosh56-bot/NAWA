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
  // M9 Slice 4 hardening: `fullyParallel: false` only serializes tests
  // WITHIN one file - separate spec files still ran in different workers
  // by default, which raced two upload-dependent specs (golden-a.spec.ts
  // and m9-slice4-golden-path.spec.ts) against the E2E fake AI client's
  // documented single-session assumption (scripts/e2e_fake_ai_client.py's
  // _resolve_hall_citation reads the LAST globally captured decision-debug
  // snapshot, not one scoped per test) - a real cross-file race, not a
  // flake, first exposed once a second upload-using spec existed. Pinning
  // to one worker makes the whole e2e/ suite serial end to end, matching
  // that documented assumption exactly.
  workers: 1,
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
