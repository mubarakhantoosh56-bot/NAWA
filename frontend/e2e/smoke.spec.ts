import { expect, test } from "@playwright/test";

const backendPort = process.env.E2E_BACKEND_PORT || "8100";
const backendHealthUrl = `http://127.0.0.1:${backendPort}/health`;

test.describe("M7 Slice 3B browser E2E infrastructure smoke", () => {
  test("real backend health endpoint is reachable", async ({ request }) => {
    const response = await request.get(backendHealthUrl);
    expect(response.status()).toBe(200);
    expect(await response.json()).toEqual({ status: "ok" });
  });

  test("production frontend serves the real login page over HTTP", async ({ page }) => {
    await page.goto("/login");

    await expect(page.getByText("NAWA", { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "Company login" })).toBeVisible();

    await expect(page.getByLabel("Company slug")).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });
});
