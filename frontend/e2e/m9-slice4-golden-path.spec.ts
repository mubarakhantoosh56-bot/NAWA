import { expect, test } from "@playwright/test";

// M9 Slice 4: Golden Path browser E2E - the browser-driven acceptance of
// the already-closed M9 chain (Slice 1 persistence, Slice 2 backend
// service/API, Slice 3 frontend + member source). Real login -> real
// authenticated workspace -> a real AI Recommendation (reusing the exact
// M7 Slice 3C Golden A upload+chat mechanism purely to reach a real,
// deterministic reasoning_receipt_id - see golden-a.spec.ts, whose
// Steps 1-5 this file's Steps 1-5 intentionally mirror rather than share,
// matching this repository's existing convention of duplicating fixture
// setup across E2E support files instead of importing across frozen
// files) -> real Human Decision -> real Action creation, assignment,
// status transitions, and history, all through the real Slice 2 API and
// the real Slice 3 UI. No Action/member API call in this file is mocked.
//
// Human Outcome regression: the existing Record Outcome path is exercised
// at the end (Step 12) to prove Action work has not broken it - Outcome
// remains a distinct concept from Action completion (no
// OutcomeMemory.action_id, no auto-created Outcome).
//
// Single-member note: the E2E seed (scripts/seed_jannat.py) provisions
// exactly one company member (the owner). Person-to-person reassignment
// (user A -> user B) is therefore not exercised here - it is already
// proven at the component level (ActionsPanel.test.tsx: "reassigns user A
// -> user B by selecting a different member") and the backend level
// (test_m9_slice2_action_service_api.py's assignment-mutation matrix).
// This spec instead proves the full Unassigned<->user cycle with the one
// real seeded member, which is the assignment behavior a single-member
// company actually exercises.

const backendPort = process.env.E2E_BACKEND_PORT || "8100";
const backendUrl = `http://127.0.0.1:${backendPort}`;

const marker = process.env.E2E_GOLDEN_MARKER;
const fixturePath = process.env.E2E_GOLDEN_FIXTURE_PATH;
const password = process.env.DEMO_OWNER_PASSWORD;

if (!marker || !fixturePath || !password) {
  throw new Error(
    "m9-slice4-golden-path.spec.ts requires E2E_GOLDEN_MARKER, E2E_GOLDEN_FIXTURE_PATH, and " +
      "DEMO_OWNER_PASSWORD - these are set by scripts/e2e_orchestrator.py and must never be " +
      "hardcoded in this spec. The upload+chat step is reused only to deterministically reach a " +
      "real reasoning_receipt_id (see module comment above) - this spec is not testing upload/citation.",
  );
}

test.describe("M9 Slice 4 Golden Path browser E2E", () => {
  test("real Decision -> Action -> assignment -> status -> history, through the real backend", async ({ page }) => {
    // --- Step 1-2: real login through the real UI (mirrors golden-a.spec.ts) --
    await page.goto("/login");
    await page.getByLabel("Company slug").fill("jannat-al-firdaws");
    await page.getByLabel("Email").fill("owner@jannat-local.dev");
    await page.getByLabel("Password").fill(password);

    const loginResponsePromise = page.waitForResponse(
      (response) => response.url() === `${backendUrl}/auth/login` && response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Sign in" }).click();
    const loginResponse = await loginResponsePromise;
    expect(loginResponse.status(), "real /auth/login must succeed - no auth bypass").toBe(200);

    // --- Step 3: real authenticated workspace --------------------------------
    await expect(page).toHaveURL(/\/workspace/);
    await expect(page.getByText("Company Inputs").first()).toBeVisible();

    // --- Step 4: real upload, purely to deterministically reach a real, ------
    // "aligned" AI Recommendation (the E2E fake AI client requires usable
    // evidence to exist before it will produce any response at all - see
    // scripts/e2e_fake_ai_client.py's _resolve_hall_citation).
    await page.getByLabel("Department").selectOption({ label: "Dairtna Poultry" });
    const uploadResponsePromise = page.waitForResponse(
      (response) => response.url().includes("/files/upload") && response.request().method() === "POST",
    );
    await page.locator('input[type="file"]').setInputFiles(fixturePath);
    await page.getByRole("button", { name: "Submit input" }).click();
    const uploadResponse = await uploadResponsePromise;
    expect(uploadResponse.status(), "real /files/upload must persist the file").toBe(201);
    await expect(page.getByText("Runtime status")).toBeVisible({ timeout: 30_000 });

    // --- Step 5: real AI Recommendation via real Company Memory chat ---------
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
    expect(chatBody.meta.reasoning_receipt_id, "a real reasoning_receipt_id must be present").toBeTruthy();

    // --- DECISION ANCHOR LAW: no Action surface before a Decision exists -----
    await expect(page.getByRole("button", { name: "Record Decision" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Create Action" })).not.toBeVisible();
    await expect(page.getByText("Actions", { exact: true })).not.toBeVisible();

    // --- Step 6: real Human Decision, no AI prefill ---------------------------
    await page.getByRole("button", { name: "Record Decision" }).click();
    const decisionField = page.getByLabel("Decision");
    await expect(decisionField).toHaveValue("");
    await decisionField.fill("Approve a focused capacity review for the Golden Journey Hall.");

    const membersResponsePromise = page.waitForResponse(
      (response) => response.url().includes("/company/members") && response.request().method() === "GET",
    );
    const decisionResponsePromise = page.waitForResponse(
      (response) => response.url() === `${backendUrl}/decisions` && response.request().method() === "POST",
    );
    await page.locator("form").getByRole("button", { name: "Record Decision" }).click();
    const decisionResponse = await decisionResponsePromise;
    expect(decisionResponse.status(), "real POST /decisions must succeed").toBe(201);
    const decisionBody = await decisionResponse.json();
    const decisionMemoryId: string = decisionBody.id;
    expect(decisionMemoryId, "a real decision_memory_id must be returned").toBeTruthy();
    await expect(page.getByText("Decision recorded")).toBeVisible();

    // --- DECISION ANCHOR LAW: Action surface appears only after the Decision -
    await expect(page.getByRole("button", { name: "Create Action" })).toBeVisible();

    // --- Step 7-11: real Action creation, no AI prefill, real member source --
    await page.getByRole("button", { name: "Create Action" }).click();
    const titleField = page.getByLabel("Title");
    const instructionsField = page.getByLabel("Instructions (optional)");
    await expect(titleField).toHaveValue("");
    await expect(instructionsField).toHaveValue("");

    const membersResponse = await membersResponsePromise;
    expect(membersResponse.status(), "real GET /company/members must succeed").toBe(200);
    const members: { id: string; full_name: string; email: string }[] = await membersResponse.json();
    expect(members.length, "the seeded owner must appear as an active company member").toBeGreaterThan(0);
    const ownerMember = members.find((member) => member.email === "owner@jannat-local.dev");
    expect(ownerMember, "the real seeded owner must be present in the real member source").toBeTruthy();

    const assigneeField = page.getByLabel("Assignee");
    await expect(assigneeField).toHaveValue("");
    await titleField.fill("Follow up on Golden Journey Hall capacity");
    await instructionsField.fill("Confirm the capacity review scope with the hall supervisor.");
    await assigneeField.selectOption({ label: ownerMember!.full_name });

    const actionsListResponsePromise = page.waitForResponse(
      (response) =>
        response.url().includes(`/actions?decision_memory_id=${decisionMemoryId}`) &&
        response.request().method() === "GET",
    );
    const createActionResponsePromise = page.waitForResponse(
      (response) => response.url() === `${backendUrl}/actions` && response.request().method() === "POST",
    );
    await page.locator("form").getByRole("button", { name: "Create Action" }).click();
    const createActionResponse = await createActionResponsePromise;
    expect(createActionResponse.status(), "real POST /actions must succeed").toBe(201);
    const createdAction = await createActionResponse.json();
    expect(createdAction.decision_memory_id, "the Action must be linked to this run's real Decision").toBe(
      decisionMemoryId,
    );
    expect(createdAction.assigned_user_id, "the Action must persist the explicitly selected assignee").toBe(
      ownerMember!.id,
    );

    const actionsListResponse = await actionsListResponsePromise;
    expect(actionsListResponse.status(), "real GET /actions?decision_memory_id=... must succeed").toBe(200);
    const actionsList: { id: string; decision_memory_id: string }[] = await actionsListResponse.json();
    expect(actionsList.some((action) => action.id === createdAction.id)).toBe(true);
    expect(actionsList.every((action) => action.decision_memory_id === decisionMemoryId)).toBe(true);

    // --- Step 12-13: Action appears with readable name, never a raw UUID -----
    const actionRow = page.locator("li", { hasText: "Follow up on Golden Journey Hall capacity" });
    await expect(actionRow).toBeVisible();
    await expect(actionRow.locator(".nawa-badge", { hasText: "Pending" })).toBeVisible();
    await expect(actionRow.locator(".nawa-badge", { hasText: ownerMember!.full_name })).toBeVisible();
    await expect(page.getByText(createdAction.id)).not.toBeVisible();
    await expect(page.getByText(ownerMember!.id)).not.toBeVisible();

    // --- Step 14-15: Pending -> In Progress, server-confirmed ----------------
    const startStatusResponsePromise = page.waitForResponse(
      (response) =>
        response.url() === `${backendUrl}/actions/${createdAction.id}/status` &&
        response.request().method() === "PATCH",
    );
    await actionRow.getByRole("button", { name: "Start" }).click();
    const startStatusResponse = await startStatusResponsePromise;
    expect(startStatusResponse.status(), "real PATCH /actions/{id}/status (in_progress) must succeed").toBe(200);
    expect((await startStatusResponse.json()).status).toBe("in_progress");
    await expect(actionRow.locator(".nawa-badge", { hasText: "In Progress" })).toBeVisible();

    // --- Assignment cycle (single-seeded-member proof - see module comment) --
    const unassignResponsePromise = page.waitForResponse(
      (response) =>
        response.url() === `${backendUrl}/actions/${createdAction.id}/assignee` &&
        response.request().method() === "PATCH",
    );
    await actionRow.getByRole("combobox", { name: "Assignee" }).selectOption({ label: "Unassigned" });
    const unassignResponse = await unassignResponsePromise;
    expect(unassignResponse.status(), "real PATCH /actions/{id}/assignee (null) must succeed").toBe(200);
    expect(
      unassignResponse.request().postDataJSON(),
      "unassign must send an explicit null, never an omitted field",
    ).toEqual({ assigned_user_id: null });
    expect((await unassignResponse.json()).assigned_user_id).toBeNull();
    await expect(actionRow.locator(".nawa-badge", { hasText: "Unassigned" })).toBeVisible();

    const reassignResponsePromise = page.waitForResponse(
      (response) =>
        response.url() === `${backendUrl}/actions/${createdAction.id}/assignee` &&
        response.request().method() === "PATCH",
    );
    await actionRow.getByRole("combobox", { name: "Assignee" }).selectOption({ label: ownerMember!.full_name });
    const reassignResponse = await reassignResponsePromise;
    expect(reassignResponse.status(), "real PATCH /actions/{id}/assignee (owner) must succeed").toBe(200);
    expect((await reassignResponse.json()).assigned_user_id).toBe(ownerMember!.id);
    await expect(actionRow.locator(".nawa-badge", { hasText: ownerMember!.full_name })).toBeVisible();

    // --- Step 16-17: In Progress -> Completed (terminal), server-confirmed ---
    const completeStatusResponsePromise = page.waitForResponse(
      (response) =>
        response.url() === `${backendUrl}/actions/${createdAction.id}/status` &&
        response.request().method() === "PATCH",
    );
    await actionRow.getByRole("button", { name: "Complete" }).click();
    const completeStatusResponse = await completeStatusResponsePromise;
    expect(completeStatusResponse.status(), "real PATCH /actions/{id}/status (completed) must succeed").toBe(200);
    expect((await completeStatusResponse.json()).status).toBe("completed");
    await expect(actionRow.locator(".nawa-badge", { hasText: "Completed" })).toBeVisible();

    // --- Step 18-19: terminal Action exposes no mutation controls ------------
    await expect(actionRow.getByRole("button", { name: "Start" })).not.toBeVisible();
    await expect(actionRow.getByRole("button", { name: "Complete" })).not.toBeVisible();
    await expect(actionRow.getByRole("button", { name: "Cancel Action" })).not.toBeVisible();
    await expect(actionRow.getByRole("combobox", { name: "Assignee" })).not.toBeVisible();
    await expect(actionRow.getByRole("button", { name: "Unassign" })).not.toBeVisible();

    // --- Step 20-24: real history, domain-correct null semantics -------------
    const detailResponsePromise = page.waitForResponse(
      (response) =>
        response.url() === `${backendUrl}/actions/${createdAction.id}` && response.request().method() === "GET",
    );
    await actionRow.getByRole("button", { name: "View history" }).click();
    const detailResponse = await detailResponsePromise;
    expect(detailResponse.status(), "real GET /actions/{id} (with history) must succeed").toBe(200);
    const detailBody = await detailResponse.json();
    expect(detailBody.events.length, "the real change ledger must contain more than one event").toBeGreaterThan(1);

    const historyText = (await actionRow.textContent()) ?? "";
    expect(historyText, "the initial status event must render Initial -> Pending, never Unassigned").toMatch(
      /Status: Initial . Pending/,
    );
    expect(historyText).not.toMatch(/Status: Unassigned/);
    expect(
      historyText,
      "the initial assignment event (Unassigned -> owner) must render with the resolved name",
    ).toMatch(new RegExp(`Assignment: Unassigned . ${ownerMember!.full_name}`));
    // A visible year is a loose, locale-independent proxy for "a
    // human-readable timestamp is rendered" (Founder correction #1).
    expect(historyText).toMatch(/20\d\d/);

    // No raw internal identifiers anywhere in the real rendered history.
    for (const event of detailBody.events as { id: string; changed_by_user_id: string }[]) {
      expect(historyText).not.toContain(event.id);
      expect(historyText).not.toContain(event.changed_by_user_id);
    }
    expect(historyText).not.toContain(createdAction.id);
    expect(historyText).not.toMatch(/"change_type"|"from_status"|"to_status"/);

    // --- Human Outcome regression: unaffected by Action work -----------------
    await expect(page.getByRole("button", { name: "Record Outcome" })).toBeVisible();
    await page.getByRole("button", { name: "Record Outcome" }).click();
    await page.getByLabel("Outcome Summary").fill("The capacity review confirmed no immediate risk.");
    await page.getByRole("button", { name: "Positive", exact: true }).click();

    const outcomeResponsePromise = page.waitForResponse(
      (response) => response.url() === `${backendUrl}/outcomes` && response.request().method() === "POST",
    );
    await page.locator("form").getByRole("button", { name: "Record Outcome" }).click();
    const outcomeResponse = await outcomeResponsePromise;
    expect(outcomeResponse.status(), "real POST /outcomes must still succeed after Action work").toBe(201);
    const outcomeBody = await outcomeResponse.json();
    expect(outcomeBody.decision_memory_id, "the Outcome must anchor to the same real Decision").toBe(
      decisionMemoryId,
    );
    await expect(page.getByText("Outcome recorded")).toBeVisible();
  });
});
