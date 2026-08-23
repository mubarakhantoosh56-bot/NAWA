import { expect, test } from "@playwright/test";

// M7 Slice 3C: Golden A browser E2E - the browser-driven version of the
// already-proven backend Golden Journey
// (tests/test_m7_slice1_upload_truth_bridge.py::test_m7_04_full_golden_journey_through_real_endpoints).
// Real login -> real authenticated workspace -> real upload through the
// real UI -> real chat UI asking about the just-uploaded content -> a
// deterministic, grounded response whose evidence resolves to that upload.
// Draft-confirmation (operational_event_drafts) is explicitly out of scope
// (Founder Decision 2) - this journey ends at the grounded chat citation.

const backendPort = process.env.E2E_BACKEND_PORT || "8100";
const backendUrl = `http://127.0.0.1:${backendPort}`;

const marker = process.env.E2E_GOLDEN_MARKER;
const fixturePath = process.env.E2E_GOLDEN_FIXTURE_PATH;
const password = process.env.DEMO_OWNER_PASSWORD;

if (!marker || !fixturePath || !password) {
  throw new Error(
    "golden-a.spec.ts requires E2E_GOLDEN_MARKER, E2E_GOLDEN_FIXTURE_PATH, and DEMO_OWNER_PASSWORD - " +
      "these are set by scripts/e2e_orchestrator.py and must never be hardcoded in this spec.",
  );
}

test.describe("M7 Slice 3C Golden A browser E2E", () => {
  test("real login, real upload, real chat citation of the just-uploaded file", async ({ page }) => {
    // --- Step 1: login page ------------------------------------------------
    await page.goto("/login");
    await expect(page.getByText("NAWA", { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "Company login" })).toBeVisible();
    await expect(page.getByLabel("Company slug")).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();

    // --- Step 2: real login through the real UI -----------------------------
    await page.getByLabel("Company slug").fill("jannat-al-firdaws");
    await page.getByLabel("Email").fill("owner@jannat-local.dev");
    await page.getByLabel("Password").fill(password);

    const loginResponsePromise = page.waitForResponse(
      (response) => response.url() === `${backendUrl}/auth/login` && response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Sign in" }).click();
    const loginResponse = await loginResponsePromise;
    expect(loginResponse.status(), "real /auth/login must succeed - no auth bypass").toBe(200);
    const loginBody = await loginResponse.json();
    expect(loginBody.company.slug, "authenticated company must be Jannat Al-Firdaws").toBe("jannat-al-firdaws");
    const accessToken: string = loginBody.access_token;

    // --- Step 3: real authenticated workspace, company identity confirmed --
    await expect(page).toHaveURL(/\/workspace/);
    await expect(page.getByText("Company Inputs").first()).toBeVisible();

    // --- Step 4: upload the synthetic workbook through the real file input -
    await page.getByLabel("Department").selectOption({ label: "Dairtna Poultry" });

    const uploadResponsePromise = page.waitForResponse(
      (response) => response.url().includes("/files/upload") && response.request().method() === "POST",
    );
    await page.locator('input[type="file"]').setInputFiles(fixturePath);
    await page.getByRole("button", { name: "Submit input" }).click();
    const uploadResponse = await uploadResponsePromise;
    expect(uploadResponse.status(), "real /files/upload must persist the file").toBe(201);
    const uploadedFile = await uploadResponse.json();
    expect(["ready", "processing"]).toContain(uploadedFile.status);

    // Wait for the application-visible "runtime status" result to settle
    // (Playwright auto-waiting expect, not a fixed sleep) before moving to
    // chat - this is the UI-visible evidence the upload was processed.
    await expect(page.getByText("Runtime status")).toBeVisible({ timeout: 30_000 });

    // --- Step 5: real Chat UI, asking about the uniquely-marked content ----
    // Company-wide chat (Company Memory), not a division tab: WorkspaceShell's
    // resolveWorkspaceDepartment() picks a department by department_type
    // alone (not by name/slug), and Dairtna Poultry and Caesar Beverage are
    // both seeded as "production_ai" - so a division-tab click cannot be
    // relied on to deterministically reach Dairtna Poultry specifically.
    // Company-wide chat sidesteps that pre-existing ambiguity entirely; the
    // uploaded-Truth bridge already deliberately supports a CEO/company-wide
    // chat seeing Dairtna evidence (see operational_truth_context.py's
    // _load_uploaded_truth_records docstring).
    await page.getByRole("button", { name: "Company Memory" }).click();
    await page
      .getByPlaceholder("Ask NAWA for a decision, plan, or department-specific recommendation...")
      .fill(`Give me an update on ${marker}.`);

    const chatResponsePromise = page.waitForResponse(
      (response) => response.url().includes("/ai/chat") && response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Send", exact: true }).click();
    const chatResponse = await chatResponsePromise;
    expect(chatResponse.status(), "real /ai/chat must respond successfully").toBe(200);
    const chatBody = await chatResponse.json();

    // --- Step 6: grounded response - structural/evidentiary assertions only
    // (no exact-prose assertion; the deterministic fake defines a stable
    // minimal contract, but only the structural fields below are load-bearing)
    const reasoningAssessment = chatBody.logic_json.reasoning_assessment;
    expect(reasoningAssessment.reasoning_state, "reasoning must be aligned, not degraded").toBe("aligned");

    const evidenceBasis: string[] = reasoningAssessment.recommendation_basis.evidence_basis;
    expect(
      evidenceBasis.length,
      "the response must cite at least one T# - static pilot sources are disabled " +
        "for this E2E backend, so any citation can only have come from this run's upload",
    ).toBeGreaterThan(0);
    const citedRef = evidenceBasis[0];

    // Visible, non-empty response in the real chat UI.
    await expect(page.getByText("NAWA", { exact: true }).last()).toBeVisible();

    // --- Step 7: prove the cited T# resolves to THIS run's uploaded file --
    // Uses the real, already-shipped, read-only decision-context debug
    // endpoint (GET /ai/debug/decision-context - app/api/decision_debug.py)
    // - the exact same mechanism the deterministic E2E fake AI client reads
    // to pick its citation (scripts/e2e_fake_ai_client.py). This does not
    // query the database, fabricate a T#, or add any route: it inspects the
    // real reasoning reference catalog the real /ai/chat call just built,
    // via the real session_id that real call actually used.
    const chatRequestBody = chatResponse.request().postDataJSON() as { session_id?: string };
    const sessionId = chatRequestBody.session_id;
    expect(sessionId, "the real /ai/chat request must carry a session_id to resolve its own snapshot").toBeTruthy();

    const debugResponse = await page.request.get(
      `${backendUrl}/ai/debug/decision-context?session_id=${encodeURIComponent(sessionId!)}`,
      { headers: { Authorization: `Bearer ${accessToken}` } },
    );
    expect(debugResponse.status(), "the real decision-context debug endpoint must be reachable for this run").toBe(
      200,
    );
    const debugBody = await debugResponse.json();
    expect(debugBody.enabled, "DECISION_CONTEXT_DEBUG must be enabled for this E2E backend").toBe(true);
    expect(
      Array.isArray(debugBody.snapshots) && debugBody.snapshots.length > 0,
      "a real snapshot must exist for this exact chat call's session_id",
    ).toBe(true);

    const decisionContext = debugBody.snapshots[0].decision_context;
    const truthCatalog = decisionContext?.reasoning_reference_catalog?.truth ?? {};
    expect(
      Object.prototype.hasOwnProperty.call(truthCatalog, citedRef),
      `the cited reference ${citedRef} must resolve inside the real reference catalog`,
    ).toBe(true);

    const resolvedItem = truthCatalog[citedRef]?.internal_source_item;
    expect(resolvedItem, `${citedRef} must resolve to a real internal source item`).toBeTruthy();
    const resolvedSourceFileId = resolvedItem?.source_file_id;
    expect(resolvedSourceFileId, `${citedRef}'s resolved item must carry a source_file_id`).toBeTruthy();

    expect(
      String(resolvedSourceFileId),
      "the cited evidence's source_file_id must equal THIS run's uploaded file id - " +
        "not an older E2E upload, not a different file, not a missing/unresolvable citation",
    ).toBe(String(uploadedFile.id));
  });
});
