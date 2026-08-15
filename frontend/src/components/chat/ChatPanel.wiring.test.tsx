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

import { sendChatMessage } from "@/lib/api/chat";

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
        <ChatPanel token="tok" companyId="company-123" workspaceKey="ceo" title="CEO" department={null} />
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
