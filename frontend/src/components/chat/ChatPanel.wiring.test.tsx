import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ChatPanel } from "@/components/chat/ChatPanel";
import { LanguageProvider } from "@/components/i18n/LanguageProvider";
import { chatStorageKey } from "@/lib/chat/storage";
import type { ChatResponse } from "@/lib/types";

// M7 Slice 2A Correction Round 1 (Section 15): a bounded component/
// integration test - NOT browser E2E - that renders the REAL ChatPanel,
// mocks only the network chat API, and inspects what the real save effect
// actually writes to localStorage. Most other privacy tests in this suite
// call the sanitization helpers directly; this proves the full production
// wiring end to end.

vi.mock("@/lib/api/chat", () => ({
  sendChatMessage: vi.fn(),
}));

vi.mock("@/lib/api/decisions", () => ({
  recordDecision: vi.fn(),
}));

vi.mock("@/lib/api/outcomes", () => ({
  recordOutcome: vi.fn(),
}));

import { sendChatMessage } from "@/lib/api/chat";
import { recordDecision } from "@/lib/api/decisions";
import { recordOutcome } from "@/lib/api/outcomes";
import { ApiError } from "@/lib/api/client";

function overBroadResponse(): ChatResponse {
  const payload = {
    ceo_text: "Hall 2 production is on track.",
    logic_json: { should_never_persist: true, reasoning_assessment: { confidence: 80 } },
    followup_question: "Would you like the weekly trend as well?",
    meta: {
      company_id: "company-123",
      session_id: "session-1",
      parse_ok: true,
      memory_injected: true,
      events_count: 2,
      context: {
        operational_events_bridge: { status: "ok" },
        truth_context_bridge: { status: "ok" },
        company_brain_bridge: { status: "ok" },
        decision_context: {
          department: { key: "ceo", name: "CEO", scope: "company_wide" },
          operational_events: [{ summary: "leaked event should not persist" }],
          // A hypothetical backend regression sending more than the
          // allowlist promises - the frontend boundary must still hold.
          operational_truth_context: [{ leaked: "should never persist" }],
          company_brain_context: [{ leaked: "confidential doctrine" }],
        },
        explainability: {
          cited_evidence: [
            {
              id: "e1",
              label: "bird_balance",
              filename: "hall2_daily_report.xlsx",
              report_date: "2026-06-01",
              entity: { type: "production_hall", reference: "2" },
              epistemic_origin: "observed",
              source_time_status: "authoritative",
              source_file_id: "b6e6b8f0-1111-2222-3333-444455556666",
            },
          ],
          cited_company_basis: [
            { id: "c1", label: "Feed sourcing priority", type: "POLICY", statement: "Prefer local feed suppliers." },
          ],
          confidence: { value: 80, band: "high", drivers: [] },
          reasoning_state: "aligned",
          operational_assessment: "Hall 2 trend reviewed against current evidence.",
          company_brain_alignment: "supported by current evidence",
          tensions: [],
          evidence_gaps: [],
          risk_assessment: "Low risk given current evidence.",
          missing_evidence: [
            {
              id: "m1",
              label: "water_consumption",
              filename: null,
              report_date: null,
              entity: null,
              epistemic_origin: null,
              source_time_status: null,
              // Defense-in-depth: a hypothetical backend regression leaking
              // internal provenance through the new missing_evidence field too.
              source_file_id: "cccc0000-1111-2222-3333-444455556666",
            },
          ],
        },
      },
    },
  };
  return payload as unknown as ChatResponse;
}

describe("ChatPanel real persistence wiring (Section 15)", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.mocked(sendChatMessage).mockReset();
  });

  it("persists only sanitized content after a real submit + save-effect cycle, and renders ExecutiveReasoningPanel without any raw LogicPanel (Section 35)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(overBroadResponse());

    const user = userEvent.setup();
    const { container } = render(
      <LanguageProvider>
        <ChatPanel
          token="tok"
          companyId="company-123"
          workspaceKey="ceo"
          title="CEO"
          department={null}
          canRecordDecisions={false}
        />
      </LanguageProvider>,
    );

    const textarea = screen.getByPlaceholderText(/Ask NAWA/i);
    await user.type(textarea, "What is the Hall 2 status?");
    await user.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByText("Hall 2 production is on track.")).toBeInTheDocument();
    });

    // ExecutiveReasoningPanel renders with the real submitted response.
    expect(screen.getByText("Executive Reasoning")).toBeInTheDocument();
    expect(screen.getByText("Aligned")).toBeInTheDocument();
    expect(screen.getByText("Hall 2 trend reviewed against current evidence.")).toBeInTheDocument();
    expect(screen.getByText("supported by current evidence")).toBeInTheDocument();
    expect(screen.getByText("bird_balance")).toBeInTheDocument();
    expect(screen.getByText("Feed sourcing priority")).toBeInTheDocument();
    expect(screen.getByText("water_consumption")).toBeInTheDocument();
    expect(screen.getByText("Low risk given current evidence.")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();

    // UI-13: raw LogicPanel is entirely absent from normal UX - no
    // "Decision logic" debug toggle, no raw JSON dump, no <details>/<pre>.
    expect(screen.queryByText("Decision logic")).not.toBeInTheDocument();
    expect(container.querySelector("pre")).toBeNull();
    expect(container.querySelector("details")).toBeNull();

    // UI-08: numeric confidence value (80) is never rendered as visible text.
    expect(container.textContent).not.toMatch(/80/);
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();

    // UI-14: no internal T#/CB#/UUID/path visible anywhere in the DOM.
    expect(container.textContent).not.toContain("source_file_id");
    expect(container.textContent).not.toContain("b6e6b8f0-1111-2222-3333-444455556666");
    expect(container.textContent).not.toContain("cccc0000-1111-2222-3333-444455556666");
    expect(container.textContent).not.toMatch(/\bT\d+\b/);
    expect(container.textContent).not.toMatch(/\bCB\d+\b/);

    await waitFor(() => {
      const raw = window.localStorage.getItem(chatStorageKey("company-123"));
      expect(raw).toBeTruthy();
    });

    const raw = window.localStorage.getItem(chatStorageKey("company-123"))!;

    // Safe visible content persisted.
    expect(raw).toContain("Hall 2 production is on track.");
    expect(raw).toContain("Would you like the weekly trend as well?");
    expect(raw).toContain("bird_balance");
    expect(raw).toContain("aligned");
    expect(raw).toContain("water_consumption");

    // logic_json absent.
    expect(raw).not.toContain("should_never_persist");
    expect(raw).not.toContain("logic_json");

    // meta.context absent (only the sanitized PersistedChatMeta survives).
    expect(raw).not.toContain("operational_events_bridge");
    expect(raw).not.toContain("truth_context_bridge");
    expect(raw).not.toContain("company_brain_bridge");
    expect(raw).not.toContain("decision_context");
    expect(raw).not.toContain("operational_truth_context");
    expect(raw).not.toContain("company_brain_context");
    expect(raw).not.toContain("leaked event should not persist");
    expect(raw).not.toContain("confidential doctrine");

    // Unsafe explainability extras / internal UUID absent, including from
    // the new missing_evidence field.
    expect(raw).not.toContain("source_file_id");
    expect(raw).not.toContain("b6e6b8f0-1111-2222-3333-444455556666");
    expect(raw).not.toContain("cccc0000-1111-2222-3333-444455556666");
  });
});

// ---------------------------------------------------------------------------
// M8 Slice 3B-2: Record Decision
// ---------------------------------------------------------------------------

function minimalResponse(options: { ceoText?: string; reasoningReceiptId?: string | null } = {}): ChatResponse {
  const payload = {
    ceo_text: options.ceoText ?? "Approve the focused expansion plan.",
    logic_json: { reasoning_assessment: { confidence: 70 } },
    followup_question: null,
    meta: {
      company_id: "company-123",
      session_id: "session-1",
      parse_ok: true,
      memory_injected: false,
      events_count: 0,
      reasoning_receipt_id: options.reasoningReceiptId === undefined ? "receipt-1" : options.reasoningReceiptId,
      context: {},
    },
  };
  return payload as unknown as ChatResponse;
}

async function sendOneMessage(user: ReturnType<typeof userEvent.setup>) {
  const textarea = screen.getByPlaceholderText(/Ask NAWA/i);
  await user.type(textarea, "What should we decide?");
  await user.click(screen.getByRole("button", { name: /send/i }));
  await waitFor(() => {
    expect(screen.queryByPlaceholderText(/Ask NAWA/i)).toHaveValue("");
  });
}

describe("ChatPanel Record Decision (M8 Slice 3B-2)", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.mocked(sendChatMessage).mockReset();
    vi.mocked(recordDecision).mockReset();
  });

  it("shows Record Decision for an assistant turn with a receipt id when permitted (items 5, 9)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <ChatPanel
          token="tok"
          companyId="company-123"
          workspaceKey="ceo"
          title="CEO"
          department={null}
          canRecordDecisions={true}
        />
      </LanguageProvider>,
    );

    await sendOneMessage(user);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Record Decision" })).toBeInTheDocument();
    });
  });

  it("does not show Record Decision when the assistant turn has no receipt id (item 6)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse({ reasoningReceiptId: null }));
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <ChatPanel
          token="tok"
          companyId="company-123"
          workspaceKey="ceo"
          title="CEO"
          department={null}
          canRecordDecisions={true}
        />
      </LanguageProvider>,
    );

    await sendOneMessage(user);

    await waitFor(() => {
      expect(screen.getByText("Approve the focused expansion plan.")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Record Decision" })).not.toBeInTheDocument();
  });

  it("does not show Record Decision when the caller lacks memory.write, even with a receipt id (items 8, 34)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <ChatPanel
          token="tok"
          companyId="company-123"
          workspaceKey="ceo"
          title="CEO"
          department={null}
          canRecordDecisions={false}
        />
      </LanguageProvider>,
    );

    await sendOneMessage(user);

    await waitFor(() => {
      expect(screen.getByText("Approve the focused expansion plan.")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Record Decision" })).not.toBeInTheDocument();
  });

  it("never shows the action on the user's own message bubble (item 7)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <ChatPanel
          token="tok"
          companyId="company-123"
          workspaceKey="ceo"
          title="CEO"
          department={null}
          canRecordDecisions={true}
        />
      </LanguageProvider>,
    );

    await sendOneMessage(user);

    await waitFor(() => {
      expect(screen.getAllByRole("button", { name: "Record Decision" })).toHaveLength(1);
    });
  });

  it("opens a blank inline form on click - decision empty, no AI-text prefill, no situation selector (items 11-15)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <ChatPanel
          token="tok"
          companyId="company-123"
          workspaceKey="ceo"
          title="CEO"
          department={null}
          canRecordDecisions={true}
        />
      </LanguageProvider>,
    );

    await sendOneMessage(user);
    await user.click(await screen.findByRole("button", { name: "Record Decision" }));

    const decisionField = screen.getByLabelText("Decision") as HTMLTextAreaElement;
    const rationaleField = screen.getByLabelText("Rationale") as HTMLTextAreaElement;
    expect(decisionField.value).toBe("");
    expect(decisionField.value).not.toContain("Approve the focused expansion plan.");
    expect(rationaleField.value).toBe("");
    expect(screen.queryByLabelText(/situation/i)).not.toBeInTheDocument();

    // item 16: submit disabled while decision is blank.
    expect(screen.getByRole("button", { name: "Record Decision" })).toBeDisabled();
  });

  it("submits exactly the four allowed fields, with situation_id null and no forbidden fields (items 17-24)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse({ reasoningReceiptId: "receipt-xyz" }));
    vi.mocked(recordDecision).mockResolvedValue({
      id: "decision-1",
      reasoning_receipt_id: "receipt-xyz",
      situation_id: null,
      decision_text: "Approve expansion for 14 accounts.",
      rationale: "Cash coverage supports it.",
      status: "active",
      decided_at: "2026-08-24T00:00:00Z",
      created_at: "2026-08-24T00:00:00Z",
    });

    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <ChatPanel
          token="tok-abc"
          companyId="company-123"
          workspaceKey="ceo"
          title="CEO"
          department={null}
          canRecordDecisions={true}
        />
      </LanguageProvider>,
    );

    await sendOneMessage(user);
    await user.click(await screen.findByRole("button", { name: "Record Decision" }));
    await user.type(screen.getByLabelText("Decision"), "Approve expansion for 14 accounts.");
    await user.type(screen.getByLabelText("Rationale"), "Cash coverage supports it.");
    await user.click(screen.getByRole("button", { name: "Record Decision" }));

    await waitFor(() => {
      expect(recordDecision).toHaveBeenCalledTimes(1);
    });

    const [token, payload] = vi.mocked(recordDecision).mock.calls[0];
    expect(token).toBe("tok-abc");
    expect(Object.keys(payload).sort()).toEqual(
      ["decision_text", "rationale", "reasoning_receipt_id", "situation_id"].sort(),
    );
    expect(payload).toEqual({
      reasoning_receipt_id: "receipt-xyz",
      decision_text: "Approve expansion for 14 accounts.",
      rationale: "Cash coverage supports it.",
      situation_id: null,
    });
  });

  it("prevents a second submission while pending and shows recorded state on success (items 18-19 pending, 25-31)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    let resolveRecord: (value: {
      id: string;
      reasoning_receipt_id: string;
      situation_id: string | null;
      decision_text: string;
      rationale: string | null;
      status: string;
      decided_at: string;
      created_at: string;
    }) => void = () => undefined;
    vi.mocked(recordDecision).mockReturnValue(
      new Promise((resolve) => {
        resolveRecord = resolve;
      }),
    );

    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <ChatPanel
          token="tok"
          companyId="company-123"
          workspaceKey="ceo"
          title="CEO"
          department={null}
          canRecordDecisions={true}
        />
      </LanguageProvider>,
    );

    await sendOneMessage(user);
    await user.click(await screen.findByRole("button", { name: "Record Decision" }));
    await user.type(screen.getByLabelText("Decision"), "Approve the plan.");

    const submitButton = screen.getByRole("button", { name: "Record Decision" });
    await user.click(submitButton);
    await user.click(submitButton);

    // item 26: only one client call fired despite the second click while pending.
    expect(recordDecision).toHaveBeenCalledTimes(1);

    resolveRecord({
      id: "decision-9",
      reasoning_receipt_id: "receipt-1",
      situation_id: null,
      decision_text: "Approve the plan.",
      rationale: null,
      status: "active",
      decided_at: "2026-08-24T00:00:00Z",
      created_at: "2026-08-24T00:00:00Z",
    });

    await waitFor(() => {
      expect(screen.getByText("Decision recorded")).toBeInTheDocument();
    });
    // item 30: no actionable button remains for this turn.
    expect(screen.queryByRole("button", { name: "Record Decision" })).not.toBeInTheDocument();

    // item 31: recorded_decision_id survives into localStorage.
    await waitFor(() => {
      const raw = window.localStorage.getItem(chatStorageKey("company-123"));
      expect(raw).toContain("decision-9");
    });
  });

  it("does not mark recorded on failure and lets the human retry (items 32-33)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    vi.mocked(recordDecision).mockRejectedValue(new ApiError(422, "invalid"));

    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <ChatPanel
          token="tok"
          companyId="company-123"
          workspaceKey="ceo"
          title="CEO"
          department={null}
          canRecordDecisions={true}
        />
      </LanguageProvider>,
    );

    await sendOneMessage(user);
    await user.click(await screen.findByRole("button", { name: "Record Decision" }));
    await user.type(screen.getByLabelText("Decision"), "Approve the plan.");
    await user.click(screen.getByRole("button", { name: "Record Decision" }));

    await waitFor(() => {
      expect(screen.getByText("Please enter a decision.")).toBeInTheDocument();
    });
    expect(screen.queryByText("Decision recorded")).not.toBeInTheDocument();
    // Form remains usable - submit is re-enabled with the same text intact.
    expect(screen.getByRole("button", { name: "Record Decision" })).not.toBeDisabled();
    expect((screen.getByLabelText("Decision") as HTMLTextAreaElement).value).toBe("Approve the plan.");
  });

  it("maps 403/404/422/generic failures to safe messages without leaking backend detail (items 34-37)", async () => {
    const cases: [unknown, string][] = [
      [new ApiError(403, "internal 403 detail"), "You don't have permission to record decisions."],
      [new ApiError(404, "internal 404 detail"), "This response is no longer available to record a decision against."],
      [new ApiError(422, "internal 422 detail"), "Please enter a decision."],
      [new Error("network down"), "Unable to record decision. Please try again."],
    ];

    for (const [rejection, expectedMessage] of cases) {
      window.localStorage.clear();
      vi.mocked(sendChatMessage).mockReset();
      vi.mocked(recordDecision).mockReset();
      vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
      vi.mocked(recordDecision).mockRejectedValue(rejection);

      const user = userEvent.setup();
      const { unmount } = render(
        <LanguageProvider>
          <ChatPanel
            token="tok"
            companyId="company-123"
            workspaceKey="ceo"
            title="CEO"
            department={null}
            canRecordDecisions={true}
          />
        </LanguageProvider>,
      );

      await sendOneMessage(user);
      await user.click(await screen.findByRole("button", { name: "Record Decision" }));
      await user.type(screen.getByLabelText("Decision"), "Approve the plan.");
      await user.click(screen.getByRole("button", { name: "Record Decision" }));

      await waitFor(() => {
        expect(screen.getByText(expectedMessage)).toBeInTheDocument();
      });
      expect(document.body.textContent).not.toContain("internal");

      unmount();
    }
  });
});

// ---------------------------------------------------------------------------
// M8 Slice 3C-2: Record Outcome
// ---------------------------------------------------------------------------

const RECORDED_DECISION_RESPONSE = {
  id: "decision-1",
  reasoning_receipt_id: "receipt-1",
  situation_id: null,
  decision_text: "Approve the plan.",
  rationale: null,
  status: "active",
  decided_at: "2026-08-25T00:00:00Z",
  created_at: "2026-08-25T00:00:00Z",
};

const OUTCOME_RESPONSE = {
  id: "outcome-999",
  decision_memory_id: "decision-1",
  outcome_summary: "Expansion delivered 12% lift.",
  result_state: "positive" as const,
  status: "active",
  observed_at: "2026-08-25T00:00:00Z",
  created_at: "2026-08-25T00:00:00Z",
};

function renderChatPanel(canRecordDecisions = true) {
  return render(
    <LanguageProvider>
      <ChatPanel
        token="tok"
        companyId="company-123"
        workspaceKey="ceo"
        title="CEO"
        department={null}
        canRecordDecisions={canRecordDecisions}
      />
    </LanguageProvider>,
  );
}

async function recordADecision(user: ReturnType<typeof userEvent.setup>) {
  vi.mocked(recordDecision).mockResolvedValue(RECORDED_DECISION_RESPONSE);
  await sendOneMessage(user);
  await user.click(await screen.findByRole("button", { name: "Record Decision" }));
  await user.type(screen.getByLabelText("Decision"), "Approve the plan.");
  await user.click(screen.getByRole("button", { name: "Record Decision" }));
  await waitFor(() => {
    expect(screen.getByText("Decision recorded")).toBeInTheDocument();
  });
}

describe("ChatPanel Record Outcome (M8 Slice 3C-2)", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.mocked(sendChatMessage).mockReset();
    vi.mocked(recordDecision).mockReset();
    vi.mocked(recordOutcome).mockReset();
  });

  // VISIBILITY ---------------------------------------------------------------

  it("does not show Record Outcome when no decision is recorded yet (item 1)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    renderChatPanel(true);

    await sendOneMessage(user);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Record Decision" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Record Outcome" })).not.toBeInTheDocument();
  });

  it("shows Record Outcome once a decision is recorded and permission is present (item 2)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    renderChatPanel(true);

    await recordADecision(user);

    expect(screen.getByRole("button", { name: "Record Outcome" })).toBeInTheDocument();
  });

  it("does not show Record Outcome without memory.write, even if a decision existed (item 3)", async () => {
    // canRecordDecisions=false also hides Record Decision itself, so a
    // decision can never be recorded through the UI in that case - the
    // no-permission path is proven by the absence of both actions.
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    renderChatPanel(false);

    await sendOneMessage(user);

    await waitFor(() => {
      expect(screen.getByText("Approve the focused expansion plan.")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Record Decision" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Record Outcome" })).not.toBeInTheDocument();
  });

  it("never shows the action on the user's own message bubble (item 4)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    renderChatPanel(true);

    await recordADecision(user);

    expect(screen.getAllByRole("button", { name: "Record Outcome" })).toHaveLength(1);
  });

  // FORM -----------------------------------------------------------------

  it("opens a blank form on click - summary empty, no result preselected, no AI prefill (items 5, 6, 11)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    renderChatPanel(true);

    await recordADecision(user);
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));

    const summaryField = screen.getByLabelText("Outcome Summary") as HTMLTextAreaElement;
    expect(summaryField.value).toBe("");
    expect(summaryField.value).not.toContain("Approve the focused expansion plan.");
    for (const label of ["Positive", "Negative", "Mixed", "Unknown"]) {
      expect(screen.getByRole("button", { name: label })).toHaveAttribute("aria-pressed", "false");
    }
  });

  it("submit is disabled with a blank summary even when a result is selected (item 7)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    renderChatPanel(true);

    await recordADecision(user);
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));
    await user.click(screen.getByRole("button", { name: "Positive" }));

    expect(screen.getByRole("button", { name: "Record Outcome" })).toBeDisabled();
  });

  it("submit is disabled with no result selection even when summary is filled (item 8)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    renderChatPanel(true);

    await recordADecision(user);
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));
    await user.type(screen.getByLabelText("Outcome Summary"), "Expansion delivered a lift.");

    expect(screen.getByRole("button", { name: "Record Outcome" })).toBeDisabled();
  });

  it("selecting Unknown enables submission and is distinct from no selection (items 9, 10)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    const user = userEvent.setup();
    renderChatPanel(true);

    await recordADecision(user);
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));

    expect(screen.getByRole("button", { name: "Record Outcome" })).toBeDisabled();
    await user.type(screen.getByLabelText("Outcome Summary"), "Result is not yet clear.");
    expect(screen.getByRole("button", { name: "Record Outcome" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Unknown" }));
    expect(screen.getByRole("button", { name: "Unknown" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Record Outcome" })).not.toBeDisabled();
  });

  // OBSERVED AT ------------------------------------------------------------

  it("blank observed_at sends no observed_at key in the payload (item 12)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    vi.mocked(recordOutcome).mockResolvedValue(OUTCOME_RESPONSE);
    const user = userEvent.setup();
    renderChatPanel(true);

    await recordADecision(user);
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));
    await user.type(screen.getByLabelText("Outcome Summary"), "Expansion delivered a lift.");
    await user.click(screen.getByRole("button", { name: "Positive" }));
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));

    await waitFor(() => {
      expect(recordOutcome).toHaveBeenCalledTimes(1);
    });
    const [, payload] = vi.mocked(recordOutcome).mock.calls[0];
    expect(Object.keys(payload).sort()).toEqual(["decision_memory_id", "outcome_summary", "result_state"].sort());
    expect(payload).not.toHaveProperty("observed_at");
  });

  it("a datetime-local value converts to a timezone-aware ISO string, never a naive one (items 13, 14)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    vi.mocked(recordOutcome).mockResolvedValue(OUTCOME_RESPONSE);
    const user = userEvent.setup();
    renderChatPanel(true);

    await recordADecision(user);
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));
    await user.type(screen.getByLabelText("Outcome Summary"), "Expansion delivered a lift.");
    await user.click(screen.getByRole("button", { name: "Positive" }));

    const observedAtField = screen.getByLabelText("Observed At") as HTMLInputElement;
    fireEvent.change(observedAtField, { target: { value: "2026-01-01T10:30" } });
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));

    await waitFor(() => {
      expect(recordOutcome).toHaveBeenCalledTimes(1);
    });
    const [, payload] = vi.mocked(recordOutcome).mock.calls[0];
    expect(payload.observed_at).toBe(new Date("2026-01-01T10:30").toISOString());
    expect(payload.observed_at).toMatch(/Z$/);
    expect(payload.observed_at).not.toBe("2026-01-01T10:30");
  });

  // REQUEST BOUNDARY -------------------------------------------------------

  it("submits exactly the allowed fields, trims the summary, and uses the exact backend result_state value (items 15-24)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    vi.mocked(recordOutcome).mockResolvedValue(OUTCOME_RESPONSE);
    const user = userEvent.setup();
    renderChatPanel(true);

    await recordADecision(user);
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));
    await user.type(screen.getByLabelText("Outcome Summary"), "  Expansion delivered a lift.  ");
    await user.click(screen.getByRole("button", { name: "Mixed" }));
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));

    await waitFor(() => {
      expect(recordOutcome).toHaveBeenCalledTimes(1);
    });
    const [token, payload] = vi.mocked(recordOutcome).mock.calls[0];
    expect(token).toBe("tok");
    expect(payload).toEqual({
      decision_memory_id: "decision-1",
      outcome_summary: "Expansion delivered a lift.",
      result_state: "mixed",
    });
    for (const forbidden of [
      "company_id",
      "recorded_by_user_id",
      "user_id",
      "status",
      "created_at",
      "evidence_refs",
      "company_brain_refs",
      "response_snapshot",
      "superseded_by",
      "supersedes_id",
      "old_outcome_id",
    ]) {
      expect(payload).not.toHaveProperty(forbidden);
    }
  });

  // PENDING ----------------------------------------------------------------

  it("a rapid double click while pending fires exactly one POST /outcomes (item 25)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    let resolveRecord: (value: typeof OUTCOME_RESPONSE) => void = () => undefined;
    vi.mocked(recordOutcome).mockReturnValue(
      new Promise((resolve) => {
        resolveRecord = resolve;
      }),
    );
    const user = userEvent.setup();
    renderChatPanel(true);

    await recordADecision(user);
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));
    await user.type(screen.getByLabelText("Outcome Summary"), "Expansion delivered a lift.");
    await user.click(screen.getByRole("button", { name: "Positive" }));

    const submitButton = screen.getByRole("button", { name: "Record Outcome" });
    await user.click(submitButton);
    await user.click(submitButton);

    expect(recordOutcome).toHaveBeenCalledTimes(1);
    resolveRecord(OUTCOME_RESPONSE);
    await waitFor(() => {
      expect(screen.getByText("Outcome recorded")).toBeInTheDocument();
    });
  });

  // SUCCESS ------------------------------------------------------------------

  it("shows a non-final confirmation and Record another outcome, never exposes the outcome id, and never permanently locks (items 26-32)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    vi.mocked(recordOutcome).mockResolvedValue(OUTCOME_RESPONSE);
    const user = userEvent.setup();
    const { container } = renderChatPanel(true);

    await recordADecision(user);
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));
    await user.type(screen.getByLabelText("Outcome Summary"), "Expansion delivered a lift.");
    await user.click(screen.getByRole("button", { name: "Positive" }));
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));

    await waitFor(() => {
      expect(screen.getByText("Outcome recorded")).toBeInTheDocument();
    });
    expect(container.textContent).not.toContain("outcome-999");
    expect(screen.queryByLabelText("Outcome Summary")).not.toBeInTheDocument();
    const recordAnother = screen.getByRole("button", { name: "Record another outcome" });
    expect(recordAnother).toBeInTheDocument();

    await user.click(recordAnother);
    const summaryField = screen.getByLabelText("Outcome Summary") as HTMLTextAreaElement;
    expect(summaryField.value).toBe("");
    for (const label of ["Positive", "Negative", "Mixed", "Unknown"]) {
      expect(screen.getByRole("button", { name: label })).toHaveAttribute("aria-pressed", "false");
    }

    await user.type(summaryField, "A second, independent observation.");
    await user.click(screen.getByRole("button", { name: "Negative" }));
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));

    await waitFor(() => {
      expect(recordOutcome).toHaveBeenCalledTimes(2);
    });
    expect(screen.getByText("Outcome recorded")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Record another outcome" })).toBeInTheDocument();
  });

  // FAILURE ------------------------------------------------------------------

  it("maps 403/404/422/generic failures to safe messages, preserves typed input, and stays retryable (items 33-39)", async () => {
    const cases: [unknown, string][] = [
      [new ApiError(403, "internal 403 detail"), "You don't have permission to record outcomes."],
      [new ApiError(404, "internal 404 detail"), "This decision is no longer available to record an outcome against."],
      [new ApiError(422, "internal 422 detail"), "Please check the outcome details."],
      [new Error("network down"), "Unable to record outcome. Please try again."],
    ];

    for (const [rejection, expectedMessage] of cases) {
      window.localStorage.clear();
      vi.mocked(sendChatMessage).mockReset();
      vi.mocked(recordDecision).mockReset();
      vi.mocked(recordOutcome).mockReset();
      vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
      vi.mocked(recordOutcome).mockRejectedValue(rejection);

      const user = userEvent.setup();
      const { unmount } = renderChatPanel(true);

      await recordADecision(user);
      await user.click(screen.getByRole("button", { name: "Record Outcome" }));
      await user.type(screen.getByLabelText("Outcome Summary"), "Expansion delivered a lift.");
      await user.click(screen.getByRole("button", { name: "Positive" }));
      await user.click(screen.getByRole("button", { name: "Record Outcome" }));

      await waitFor(() => {
        expect(screen.getByText(expectedMessage)).toBeInTheDocument();
      });
      expect(document.body.textContent).not.toContain("internal");
      expect(screen.queryByText("Outcome recorded")).not.toBeInTheDocument();
      expect((screen.getByLabelText("Outcome Summary") as HTMLTextAreaElement).value).toBe(
        "Expansion delivered a lift.",
      );
      expect(screen.getByRole("button", { name: "Positive" })).toHaveAttribute("aria-pressed", "true");
      expect(screen.getByRole("button", { name: "Record Outcome" })).not.toBeDisabled();

      unmount();
    }
  });

  // PRIVACY --------------------------------------------------------------

  it("never persists the outcome id, summary, result_state, or observed_at to localStorage (items 40-43)", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(minimalResponse());
    vi.mocked(recordOutcome).mockResolvedValue(OUTCOME_RESPONSE);
    const user = userEvent.setup();
    renderChatPanel(true);

    await recordADecision(user);
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));
    await user.type(screen.getByLabelText("Outcome Summary"), "Expansion delivered a lift.");
    await user.click(screen.getByRole("button", { name: "Positive" }));
    const observedAtField = screen.getByLabelText("Observed At") as HTMLInputElement;
    fireEvent.change(observedAtField, { target: { value: "2026-01-01T10:30" } });
    await user.click(screen.getByRole("button", { name: "Record Outcome" }));

    await waitFor(() => {
      expect(screen.getByText("Outcome recorded")).toBeInTheDocument();
    });

    const raw = window.localStorage.getItem(chatStorageKey("company-123"));
    expect(raw).toBeTruthy();
    expect(raw).not.toContain("outcome-999");
    expect(raw).not.toContain("Expansion delivered a lift.");
    expect(raw).not.toContain("positive");
    expect(raw).not.toContain("2026-01-01T10:30");
  });
});
