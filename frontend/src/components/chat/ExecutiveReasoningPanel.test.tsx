import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { ExecutiveReasoningPanel } from "@/components/chat/ExecutiveReasoningPanel";
import { LanguageProvider } from "@/components/i18n/LanguageProvider";
import { LANGUAGE_STORAGE_KEY } from "@/lib/i18n";
import type { Explainability } from "@/lib/types";

// M7 Slice 2B (Step 2B-3): ExecutiveReasoningPanel tested against safe
// FIXTURES only - built and verified before any ChatPanel integration
// (Section 31: "do not skip the fixture-before-live integration order").
// Fixtures use the exact sanitized Explainability shape the backend/
// frontend sanitizer boundary produces - never a raw T#/CB#/logic_json
// shape.

function baseExplainability(overrides: Partial<Explainability> = {}): Explainability {
  return {
    cited_evidence: [],
    cited_company_basis: [],
    cited_organizational_memory: [],
    confidence: null,
    reasoning_state: null,
    operational_assessment: null,
    company_brain_alignment: null,
    tensions: [],
    evidence_gaps: [],
    risk_assessment: null,
    missing_evidence: [],
    ...overrides,
  };
}

const alignedFixture: Explainability = baseExplainability({
  reasoning_state: "aligned",
  operational_assessment: "Hall 2 production trend is stable given current evidence.",
  company_brain_alignment: "supported by current evidence",
  risk_assessment: "Low risk given current trend.",
  cited_evidence: [
    {
      id: "e1",
      label: "bird_balance",
      filename: "hall2_daily_report.xlsx",
      report_date: "2026-06-01",
      entity: { type: "production_hall", reference: "2" },
      epistemic_origin: "observed",
      source_time_status: "authoritative",
    },
  ],
  cited_company_basis: [
    { id: "c1", label: "Feed sourcing priority", type: "POLICY", statement: "Prefer local feed suppliers." },
  ],
  confidence: { value: 83, band: "high", drivers: [] },
});

const tensionFixture: Explainability = baseExplainability({
  reasoning_state: "tension",
  operational_assessment: "Production is stable but company policy expects growth this quarter.",
  company_brain_alignment: "partially supported",
  tensions: ["Evidence shows a stable trend while company priority calls for accelerated growth."],
  cited_evidence: [
    {
      id: "e1",
      label: "daily_production_rate",
      filename: "hall2_daily_report.xlsx",
      report_date: null,
      entity: { type: "production_hall", reference: "2" },
      epistemic_origin: "derived",
      source_time_status: "unresolved",
    },
  ],
  cited_company_basis: [
    { id: "c1", label: "Growth priority", type: "PREFERENCE", statement: "Pursue regional expansion." },
  ],
  risk_assessment: "Moderate risk if growth targets are pursued without confirming capacity.",
  confidence: {
    value: 55,
    band: "moderate",
    drivers: ["unresolved_source_time", "conflicted_company_basis"],
  },
});

const insufficientEvidenceFixture: Explainability = baseExplainability({
  reasoning_state: "insufficient_evidence",
  operational_assessment: "Not enough evidence is available to assess Hall 2 water consumption.",
  company_brain_alignment: "cannot determine",
  evidence_gaps: ["Water consumption reading is missing for Hall 2."],
  missing_evidence: [
    {
      id: "m1",
      label: "water_consumption",
      filename: null,
      report_date: null,
      entity: { type: "production_hall", reference: "2" },
      epistemic_origin: null,
      source_time_status: null,
    },
  ],
  risk_assessment: "Cannot assess risk without the missing evidence.",
  confidence: { value: 20, band: "low", drivers: ["missing_evidence"] },
});

async function renderInLanguage(explainability: Explainability | null, language: "en" | "ar" = "en") {
  if (language === "ar") {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "ar");
  }
  const view = render(
    <LanguageProvider>
      <ExecutiveReasoningPanel explainability={explainability} />
    </LanguageProvider>,
  );
  if (language === "ar") {
    await waitFor(() => expect(document.documentElement.dir).toBe("rtl"));
  }
  return view;
}

describe("ExecutiveReasoningPanel", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.dir = "ltr";
  });

  it("UI-01: renders the aligned state with its supporting evidence/basis and confidence band", async () => {
    await renderInLanguage(alignedFixture);
    expect(screen.getByText("Aligned")).toBeInTheDocument();
    expect(screen.getByText("Hall 2 production trend is stable given current evidence.")).toBeInTheDocument();
    expect(screen.getByText("supported by current evidence")).toBeInTheDocument();
    expect(screen.getByText("bird_balance")).toBeInTheDocument();
    expect(screen.getByText("Feed sourcing priority")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    // No tensions for an aligned turn.
    expect(screen.queryByText("Tensions")).not.toBeInTheDocument();
  });

  it("UI-02: renders the tension state with tensions and neutral framing", async () => {
    await renderInLanguage(tensionFixture);
    expect(screen.getByText("Tension")).toBeInTheDocument();
    expect(
      screen.getByText("Evidence shows a stable trend while company priority calls for accelerated growth."),
    ).toBeInTheDocument();
    expect(screen.getByText("partially supported")).toBeInTheDocument();
    // Constitution V.2: neither side is declared the automatic winner.
    expect(screen.queryByText(/overrides/i)).not.toBeInTheDocument();
  });

  it("UI-03: renders the insufficient_evidence state as a decision-limitation state, not an error", async () => {
    await renderInLanguage(insufficientEvidenceFixture);
    expect(screen.getByText("Insufficient Evidence")).toBeInTheDocument();
    expect(screen.getByText("cannot determine")).toBeInTheDocument();
    expect(screen.getByText("Water consumption reading is missing for Hall 2.")).toBeInTheDocument();
    expect(screen.getByText("water_consumption")).toBeInTheDocument();
    // Never framed as a software error.
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
  });

  it("UI-04: renders cited evidence human-readably, and an empty state when nothing is cited", async () => {
    const first = await renderInLanguage(alignedFixture);
    expect(screen.getByText("hall2_daily_report.xlsx")).toBeInTheDocument();
    expect(screen.getByText("2026-06-01")).toBeInTheDocument();
    expect(screen.getByText(/production_hall: 2/)).toBeInTheDocument();
    first.unmount();

    await renderInLanguage(baseExplainability({ reasoning_state: "aligned" }));
    expect(screen.getByText("No specific evidence cited.")).toBeInTheDocument();
  });

  it("UI-05: renders cited Company Brain basis human-readably, and an empty state when nothing is cited", async () => {
    const first = await renderInLanguage(alignedFixture);
    expect(screen.getByText("Feed sourcing priority")).toBeInTheDocument();
    expect(screen.getByText("POLICY")).toBeInTheDocument();
    expect(screen.getByText("Prefer local feed suppliers.")).toBeInTheDocument();
    first.unmount();

    await renderInLanguage(baseExplainability({ reasoning_state: "aligned" }));
    expect(screen.getByText("No specific Company Brain basis cited.")).toBeInTheDocument();
  });

  it("UI-06: renders evidence_gaps prose and structured missing_evidence as distinct sub-items", async () => {
    await renderInLanguage(insufficientEvidenceFixture);
    // Both concepts appear under the same "Missing Evidence" heading.
    expect(screen.getByText("Missing Evidence")).toBeInTheDocument();
    // The prose gap.
    expect(screen.getByText("Water consumption reading is missing for Hall 2.")).toBeInTheDocument();
    // The structured gap item, never deduplicated/merged into the prose.
    expect(screen.getByText("water_consumption")).toBeInTheDocument();
  });

  it("UI-07: renders confidence band and deterministic translated drivers", async () => {
    await renderInLanguage(tensionFixture);
    expect(screen.getByText("Moderate")).toBeInTheDocument();
    expect(screen.getByText("Reduced because source freshness is unresolved.")).toBeInTheDocument();
    expect(screen.getByText("Reduced because Company Brain context is conflicted.")).toBeInTheDocument();
  });

  it("UI-08: never renders the numeric confidence value", async () => {
    const { container } = await renderInLanguage(alignedFixture);
    // confidence.value is 83 in this fixture - it must never appear as
    // visible text, nor as a percentage/score anywhere in the panel.
    expect(container.textContent).not.toMatch(/83/);
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\/\s*100/)).not.toBeInTheDocument();
  });

  it("UI-09: handles unresolved source time safely without implying freshness", async () => {
    await renderInLanguage(tensionFixture);
    expect(screen.getByText("Freshness unresolved")).toBeInTheDocument();
    // DERIVED evidence with no report_date renders without crashing and
    // without inventing a date.
    expect(screen.getByText("daily_production_rate")).toBeInTheDocument();
    expect(screen.getByText("Derived")).toBeInTheDocument();
  });

  it("UI-10: a legacy/no-reasoning response omits the panel entirely without crashing", async () => {
    const first = await renderInLanguage(null);
    expect(first.container.firstChild).toBeNull();
    first.unmount();

    const second = await renderInLanguage(
      baseExplainability({
        cited_evidence: [
          { id: "e1", label: "x", filename: null, report_date: null, entity: null, epistemic_origin: null, source_time_status: null },
        ],
      }),
    );
    expect(second.container.firstChild).toBeNull();
  });

  it("UI-11: Arabic labels render when the language is Arabic", async () => {
    await renderInLanguage(alignedFixture, "ar");
    expect(screen.getByText("الاستدلال التنفيذي")).toBeInTheDocument();
    expect(screen.getByText("متوافق")).toBeInTheDocument();
    expect(screen.getByText("التقييم التشغيلي")).toBeInTheDocument();
  });

  it("UI-12: English labels render when the language is English", async () => {
    await renderInLanguage(alignedFixture, "en");
    expect(screen.getByText("Executive Reasoning")).toBeInTheDocument();
    expect(screen.getByText("Aligned")).toBeInTheDocument();
    expect(screen.getByText("Operational Assessment")).toBeInTheDocument();
  });

  it("UI-14: never renders internal T#/CB#/UUID/path tokens", async () => {
    await renderInLanguage(alignedFixture);
    // The opaque presentation ids (e1/c1) are used only as React keys,
    // never rendered as visible text.
    expect(screen.queryByText("e1")).not.toBeInTheDocument();
    expect(screen.queryByText("c1")).not.toBeInTheDocument();
    expect(screen.queryByText(/^T\d+$/)).not.toBeInTheDocument();
    expect(screen.queryByText(/^CB\d+$/)).not.toBeInTheDocument();
    expect(screen.queryByText(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i)).not.toBeInTheDocument();
  });

  it("UI-15: renders company_brain_alignment verbatim from the backend field, never re-mapped", async () => {
    await renderInLanguage(
      baseExplainability({
        reasoning_state: "aligned",
        // A deliberately unusual/verbatim string to prove no re-mapping occurs.
        company_brain_alignment: "partially supported",
      }),
    );
    expect(screen.getByText("partially supported")).toBeInTheDocument();
  });

  it("H02-A: Arabic mode never renders raw English technical enum labels for evidence metadata", async () => {
    const { container } = await renderInLanguage(tensionFixture, "ar");
    // The canonical DERIVED/unresolved evidence item in tensionFixture.
    expect(container.textContent).not.toContain("Observed");
    expect(container.textContent).not.toContain("Derived");
    expect(container.textContent).not.toContain("Authoritative");
    expect(container.textContent).not.toContain("Unresolved");
    // Arabic labels appear instead.
    expect(screen.getByText("مُستنتج")).toBeInTheDocument();
    expect(screen.getByText("حداثة غير مؤكدة")).toBeInTheDocument();
    // RTL remains active.
    expect(document.documentElement.dir).toBe("rtl");
  });

  it("H02-A: Arabic mode renders the Arabic label for OBSERVED + authoritative source time too", async () => {
    await renderInLanguage(alignedFixture, "ar");
    expect(screen.getByText("ملاحظ")).toBeInTheDocument();
    expect(screen.getByText("موثوق")).toBeInTheDocument();
  });

  it("H02-B: English mode renders proper English labels for evidence metadata", async () => {
    const first = await renderInLanguage(alignedFixture, "en");
    expect(screen.getByText("Observed")).toBeInTheDocument();
    expect(screen.getByText("Authoritative")).toBeInTheDocument();
    first.unmount();

    await renderInLanguage(tensionFixture, "en");
    expect(screen.getByText("Derived")).toBeInTheDocument();
    expect(screen.getByText("Freshness unresolved")).toBeInTheDocument();
  });

  it("H02-C: missing/null evidence metadata does not crash and renders no origin/freshness badge", async () => {
    // insufficientEvidenceFixture's missing_evidence item has
    // epistemic_origin: null, source_time_status: null.
    await renderInLanguage(insufficientEvidenceFixture);
    expect(screen.getByText("water_consumption")).toBeInTheDocument();
    // None of the closed-mapping labels are present for this null-metadata item.
    expect(screen.queryByText("Observed")).not.toBeInTheDocument();
    expect(screen.queryByText("Freshness unresolved")).not.toBeInTheDocument();
    expect(screen.queryByText("Authoritative")).not.toBeInTheDocument();
  });

  it("H02-D: an unexpected/unknown enum value is omitted, never dumped raw", async () => {
    const { container } = await renderInLanguage(
      baseExplainability({
        reasoning_state: "aligned",
        cited_evidence: [
          {
            id: "e1",
            label: "unusual_metric",
            filename: null,
            report_date: null,
            entity: null,
            // Not one of the canonical values - must never be rendered
            // as-is, and must not crash.
            epistemic_origin: "estimated",
            source_time_status: "pending_confirmation",
          },
        ],
      }),
    );
    expect(screen.getByText("unusual_metric")).toBeInTheDocument();
    expect(container.textContent).not.toContain("estimated");
    expect(container.textContent).not.toContain("pending_confirmation");
  });
});

// M8 Slice 4C-2: Historical Organizational Memory section - a third,
// distinct citation category. Fixtures use the exact sanitized
// CitedOrganizationalMemoryItem shape (id/decision/rationale/decided_at/
// outcomes/omitted_outcomes_count) - never a raw OM#/durable-id shape.
describe("ExecutiveReasoningPanel - Historical Organizational Memory (M8 Slice 4C-2)", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.dir = "ltr";
  });

  const omFixture: Explainability = baseExplainability({
    reasoning_state: "aligned",
    cited_organizational_memory: [
      {
        id: "h1",
        decision: "Approve expansion for 14 accounts.",
        rationale: "Cash coverage supports it.",
        decided_at: "2020-01-01T00:00:00Z",
        outcomes: [
          { result_state: "positive", summary: "Revenue grew as expected.", observed_at: "2020-02-01T00:00:00Z" },
          { result_state: "negative", summary: "Support costs rose sharply.", observed_at: "2020-03-01T00:00:00Z" },
          { result_state: "mixed", summary: "Mixed regional adoption.", observed_at: "2020-04-01T00:00:00Z" },
          { result_state: "unknown", summary: "Long-term effect not yet assessed.", observed_at: "2020-05-01T00:00:00Z" },
        ],
        omitted_outcomes_count: 3,
      },
    ],
  });

  const omNoRationaleFixture: Explainability = baseExplainability({
    reasoning_state: "aligned",
    cited_organizational_memory: [
      {
        id: "h1",
        decision: "Discontinue the pilot program.",
        rationale: null,
        decided_at: "2021-06-01T00:00:00Z",
        outcomes: [{ result_state: "unknown", summary: "No outcome recorded yet.", observed_at: "2021-07-01T00:00:00Z" }],
        omitted_outcomes_count: 0,
      },
    ],
  });

  it("1: an empty cited_organizational_memory array hides the section entirely", async () => {
    await renderInLanguage(baseExplainability({ reasoning_state: "aligned" }));
    expect(screen.queryByText("Historical Organizational Memory")).not.toBeInTheDocument();
  });

  it("2/3/4: renders the heading, supporting copy, and causality disclaimer exactly once", async () => {
    await renderInLanguage(omFixture);
    expect(screen.getByText("Historical Organizational Memory")).toBeInTheDocument();
    expect(
      screen.getByText("Prior human decisions and their recorded outcomes, cited as historical context for this recommendation."),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Recorded outcomes occurred after the decision and do not prove that the decision caused them.")
        .length,
    ).toBe(1);
  });

  it("5: renders the Decision text", async () => {
    await renderInLanguage(omFixture);
    expect(screen.getByText("Approve expansion for 14 accounts.")).toBeInTheDocument();
  });

  it("6: renders rationale when present", async () => {
    await renderInLanguage(omFixture);
    expect(screen.getByText("Cash coverage supports it.")).toBeInTheDocument();
  });

  it("7: omits the rationale row entirely when rationale is null", async () => {
    const { container } = await renderInLanguage(omNoRationaleFixture);
    expect(container.textContent).not.toMatch(/No rationale/);
    expect(container.textContent).not.toMatch(/n\/a/i);
  });

  it("8: renders decided_at", async () => {
    await renderInLanguage(omFixture);
    expect(screen.getByText(/2020-01-01T00:00:00Z/)).toBeInTheDocument();
  });

  it("9: h1 (the presentation id) is never rendered as visible text", async () => {
    await renderInLanguage(omFixture);
    expect(screen.queryByText("h1")).not.toBeInTheDocument();
    expect(screen.queryByText(/^h\d+$/)).not.toBeInTheDocument();
  });

  it("10/11/12/13: renders localized labels for positive/negative/mixed/unknown, unknown distinct", async () => {
    await renderInLanguage(omFixture);
    expect(screen.getByText("Positive")).toBeInTheDocument();
    expect(screen.getByText("Negative")).toBeInTheDocument();
    expect(screen.getByText("Mixed")).toBeInTheDocument();
    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });

  it("14: multiple Outcomes render separately, never collapsed", async () => {
    await renderInLanguage(omFixture);
    expect(screen.getByText("Revenue grew as expected.")).toBeInTheDocument();
    expect(screen.getByText("Support costs rose sharply.")).toBeInTheDocument();
    expect(screen.getByText("Mixed regional adoption.")).toBeInTheDocument();
    expect(screen.getByText("Long-term effect not yet assessed.")).toBeInTheDocument();
  });

  it("15: renders observed_at for each Outcome", async () => {
    await renderInLanguage(omFixture);
    expect(screen.getByText(/2020-02-01T00:00:00Z/)).toBeInTheDocument();
    expect(screen.getByText(/2020-05-01T00:00:00Z/)).toBeInTheDocument();
  });

  it("16: omitted_outcomes_count=0 shows no omission note", async () => {
    const { container } = await renderInLanguage(omNoRationaleFixture);
    expect(container.textContent).not.toContain("context limits");
  });

  it("17: omitted_outcomes_count>0 displays the count plus neutral omission copy", async () => {
    await renderInLanguage(omFixture);
    expect(
      screen.getByText(/3 additional recorded outcomes were omitted from the AI context/),
    ).toBeInTheDocument();
  });

  it("18/19: no final-outcome/net-result copy and no causal-proof wording beyond the one disclaimer", async () => {
    const { container } = await renderInLanguage(omFixture);
    expect(container.textContent).not.toMatch(/final outcome/i);
    expect(container.textContent).not.toMatch(/net result/i);
    expect(container.textContent).not.toMatch(/proves? causation/i);
    expect(container.textContent).not.toMatch(/guarantee/i);
  });

  it("20/21: Evidence Used and Company Brain Basis sections remain unaffected by an OM citation", async () => {
    await renderInLanguage(
      baseExplainability({
        reasoning_state: "aligned",
        cited_evidence: [
          {
            id: "e1",
            label: "bird_balance",
            filename: "hall2_daily_report.xlsx",
            report_date: "2026-06-01",
            entity: null,
            epistemic_origin: "observed",
            source_time_status: "authoritative",
          },
        ],
        cited_company_basis: [
          { id: "c1", label: "Feed sourcing priority", type: "POLICY", statement: "Prefer local feed suppliers." },
        ],
        cited_organizational_memory: omFixture.cited_organizational_memory,
      }),
    );
    expect(screen.getByText("bird_balance")).toBeInTheDocument();
    expect(screen.getByText("Feed sourcing priority")).toBeInTheDocument();
    expect(screen.getByText("Historical Organizational Memory")).toBeInTheDocument();
  });

  it("22: the Historical Organizational Memory section is distinct, appearing after Company Brain Basis and before Missing Evidence", async () => {
    const { container } = await renderInLanguage(
      baseExplainability({
        reasoning_state: "insufficient_evidence",
        cited_company_basis: [
          { id: "c1", label: "Growth priority", type: "PREFERENCE", statement: "Pursue regional expansion." },
        ],
        cited_organizational_memory: omFixture.cited_organizational_memory,
        evidence_gaps: ["Water consumption reading is missing for Hall 2."],
      }),
    );
    const text = container.textContent ?? "";
    const companyBasisIndex = text.indexOf("Company Brain Basis");
    const omIndex = text.indexOf("Historical Organizational Memory");
    const missingEvidenceIndex = text.indexOf("Missing Evidence");
    expect(companyBasisIndex).toBeGreaterThanOrEqual(0);
    expect(omIndex).toBeGreaterThan(companyBasisIndex);
    expect(missingEvidenceIndex).toBeGreaterThan(omIndex);
  });

  it("23/24/25: Arabic heading, supporting copy, and causality disclaimer render", async () => {
    await renderInLanguage(omFixture, "ar");
    expect(screen.getByText("الذاكرة المؤسسية التاريخية")).toBeInTheDocument();
    expect(
      screen.getByText("قرارات بشرية سابقة ونتائجها المسجّلة، تم الاستشهاد بها كسياق تاريخي لهذه التوصية."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("النتائج المسجّلة حدثت بعد اتخاذ القرار ولا تُثبت أن القرار كان سببًا لها."),
    ).toBeInTheDocument();
  });

  it("26: Arabic (RTL) render does not crash and keeps rtl direction active", async () => {
    await renderInLanguage(omFixture, "ar");
    expect(document.documentElement.dir).toBe("rtl");
    expect(screen.getByText("Approve expansion for 14 accounts.")).toBeInTheDocument();
  });
});
