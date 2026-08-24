import { render, screen, waitFor } from "@testing-library/react";
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

import { sendChatMessage } from "@/lib/api/chat";
import { recordDecision } from "@/lib/api/decisions";
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
