import { beforeEach, describe, expect, it } from "vitest";

import { chatStorageKey, clearAllStoredChats, clearStoredChat, sanitizeExplainability } from "@/lib/chat/storage";

// M7 Slice 2A privacy contract tests (Section 17, P6/P7 foundation - see
// AuthProvider.test.tsx for the end-to-end logout() wiring on top of this).
// Correction Round 1 additions: clearAllStoredChats (2A-F3 foundation,
// F3-D exact-prefix precision) and sanitizeExplainability (2A-F2).

beforeEach(() => {
  window.localStorage.clear();
});

describe("chatStorageKey", () => {
  it("uses the exact nawa.chat.{companyId} convention", () => {
    expect(chatStorageKey("company-123")).toBe("nawa.chat.company-123");
  });
});

describe("clearStoredChat", () => {
  it("P6: removes only the chat cache for the given company id", () => {
    window.localStorage.setItem(chatStorageKey("company-a"), JSON.stringify({ ceo: [] }));

    clearStoredChat("company-a");

    expect(window.localStorage.getItem(chatStorageKey("company-a"))).toBeNull();
  });

  it("P7: does not remove a DIFFERENT company's chat cache", () => {
    window.localStorage.setItem(chatStorageKey("company-a"), JSON.stringify({ ceo: [] }));
    window.localStorage.setItem(chatStorageKey("company-b"), JSON.stringify({ ceo: [] }));

    clearStoredChat("company-a");

    expect(window.localStorage.getItem(chatStorageKey("company-a"))).toBeNull();
    expect(window.localStorage.getItem(chatStorageKey("company-b"))).not.toBeNull();
  });

  it("P7: does not remove unrelated localStorage keys (e.g. the auth token)", () => {
    window.localStorage.setItem(chatStorageKey("company-a"), JSON.stringify({ ceo: [] }));
    window.localStorage.setItem("aimx.access_token", "some-jwt");
    window.localStorage.setItem("some.other.app.preference", "kept");

    clearStoredChat("company-a");

    expect(window.localStorage.getItem("aimx.access_token")).toBe("some-jwt");
    expect(window.localStorage.getItem("some.other.app.preference")).toBe("kept");
  });
});

describe("clearAllStoredChats (2A-F3 foundation)", () => {
  it("removes every nawa.chat.* key regardless of company", () => {
    window.localStorage.setItem(chatStorageKey("company-a"), JSON.stringify({ ceo: [] }));
    window.localStorage.setItem(chatStorageKey("company-b"), JSON.stringify({ ceo: [] }));

    clearAllStoredChats();

    expect(window.localStorage.getItem(chatStorageKey("company-a"))).toBeNull();
    expect(window.localStorage.getItem(chatStorageKey("company-b"))).toBeNull();
  });

  it("F3-D: only removes keys with the EXACT nawa.chat. prefix - no wildcard/prefix bug", () => {
    window.localStorage.setItem(chatStorageKey("company-a"), JSON.stringify({ ceo: [] }));
    window.localStorage.setItem("nawa.chatting.preference", "kept");
    window.localStorage.setItem("nawa.preference", "kept");
    window.localStorage.setItem("other.app.data", "kept");
    window.localStorage.setItem("aimx.access_token", "kept");

    clearAllStoredChats();

    expect(window.localStorage.getItem(chatStorageKey("company-a"))).toBeNull();
    expect(window.localStorage.getItem("nawa.chatting.preference")).toBe("kept");
    expect(window.localStorage.getItem("nawa.preference")).toBe("kept");
    expect(window.localStorage.getItem("other.app.data")).toBe("kept");
    expect(window.localStorage.getItem("aimx.access_token")).toBe("kept");
  });

  it("does not throw when there is nothing to clear", () => {
    expect(() => clearAllStoredChats()).not.toThrow();
  });
});

describe("sanitizeExplainability (2A-F2)", () => {
  it("returns null for non-object/absent input without throwing", () => {
    expect(sanitizeExplainability(null)).toBeNull();
    expect(sanitizeExplainability(undefined)).toBeNull();
    expect(sanitizeExplainability("not an object")).toBeNull();
    expect(sanitizeExplainability(42)).toBeNull();
  });

  it("keeps only the allowlisted evidence/company-basis/confidence fields", () => {
    const sanitized = sanitizeExplainability({
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
        { id: "c1", label: "Feed sourcing priority", type: "POLICY", statement: "Prefer local suppliers." },
      ],
      confidence: { value: 80, band: "high", drivers: ["missing_evidence"] },
    });

    expect(sanitized).toEqual({
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
        { id: "c1", label: "Feed sourcing priority", type: "POLICY", statement: "Prefer local suppliers." },
      ],
      confidence: { value: 80, band: "high", drivers: ["missing_evidence"] },
      reasoning_state: null,
      operational_assessment: null,
      company_brain_alignment: null,
      tensions: [],
      evidence_gaps: [],
      risk_assessment: null,
      missing_evidence: [],
    });
  });

  it("strips unapproved extra fields nested inside otherwise-valid items", () => {
    const sanitized = sanitizeExplainability({
      cited_evidence: [
        {
          id: "e1",
          label: "bird_balance",
          filename: "hall2_daily_report.xlsx",
          report_date: null,
          entity: { type: "production_hall", reference: "2", extra_secret: "leak" },
          epistemic_origin: "observed",
          source_time_status: "authoritative",
          source_file_id: "b6e6b8f0-1111-2222-3333-444455556666",
          source_company_id: "aaaa0000-1111-2222-3333-444455556666",
          source_department_id: "cccc0000-1111-2222-3333-444455556666",
          filesystem_path: "/var/data/hall2.xlsx",
          storage_path: "s3://bucket/hall2.xlsx",
          secret_extra: "leak",
        },
      ],
      cited_company_basis: [
        {
          id: "c1",
          label: "Feed sourcing priority",
          type: "POLICY",
          statement: "Prefer local suppliers.",
          authority: "authoritative",
          source: "DAIRTNA_COMPANY_BRAIN",
          provenance_note: "leak",
          secret_extra: "leak",
        },
      ],
      confidence: { value: 80, band: "high", drivers: ["missing_evidence", "made_up_driver"], extra_internal: "leak" },
    });

    const serialized = JSON.stringify(sanitized);
    expect(serialized).not.toContain("extra_secret");
    expect(serialized).not.toContain("source_file_id");
    expect(serialized).not.toContain("source_company_id");
    expect(serialized).not.toContain("source_department_id");
    expect(serialized).not.toContain("b6e6b8f0-1111-2222-3333-444455556666");
    expect(serialized).not.toContain("filesystem_path");
    expect(serialized).not.toContain("storage_path");
    expect(serialized).not.toContain("authority");
    // "source" itself is not checked as a bare substring - it would false-
    // positive against the legitimately allowed "source_time_status"
    // field; the specific unsafe source_* keys are already checked above.
    expect(serialized).not.toContain("DAIRTNA_COMPANY_BRAIN");
    expect(serialized).not.toContain("provenance_note");
    expect(serialized).not.toContain("secret_extra");
    expect(serialized).not.toContain("extra_internal");
    expect(serialized).not.toContain("made_up_driver");
    // Safe fields still present.
    expect(sanitized?.cited_evidence[0].entity).toEqual({ type: "production_hall", reference: "2" });
    expect(sanitized?.confidence?.drivers).toEqual(["missing_evidence"]);
  });

  it("drops items missing a required id rather than fabricating one", () => {
    const sanitized = sanitizeExplainability({
      cited_evidence: [{ label: "no id here" }],
      cited_company_basis: [{ label: "also no id" }],
      confidence: null,
    });
    expect(sanitized?.cited_evidence).toEqual([]);
    expect(sanitized?.cited_company_basis).toEqual([]);
  });

  it("drops confidence entirely if band is not a closed enum value, rather than guessing", () => {
    const sanitized = sanitizeExplainability({
      cited_evidence: [],
      cited_company_basis: [],
      confidence: { value: 80, band: "extremely-confident", drivers: [] },
    });
    expect(sanitized?.confidence).toBeNull();
  });

  it("handles missing/malformed arrays without throwing", () => {
    expect(() => sanitizeExplainability({})).not.toThrow();
    expect(sanitizeExplainability({})).toEqual({
      cited_evidence: [],
      cited_company_basis: [],
      confidence: null,
      reasoning_state: null,
      operational_assessment: null,
      company_brain_alignment: null,
      tensions: [],
      evidence_gaps: [],
      risk_assessment: null,
      missing_evidence: [],
    });
    expect(() => sanitizeExplainability({ cited_evidence: "not-an-array", cited_company_basis: 42 })).not.toThrow();
  });
});

describe("sanitizeExplainability - Slice 2B fields (P2B)", () => {
  it("P2B-01: keeps a valid closed-enum reasoning_state", () => {
    expect(sanitizeExplainability({ reasoning_state: "tension" })?.reasoning_state).toBe("tension");
    expect(sanitizeExplainability({ reasoning_state: "aligned" })?.reasoning_state).toBe("aligned");
    expect(sanitizeExplainability({ reasoning_state: "insufficient_evidence" })?.reasoning_state).toBe(
      "insufficient_evidence",
    );
  });

  it("P2B-09: drops an unrecognized reasoning_state rather than fabricating a fourth state", () => {
    expect(sanitizeExplainability({ reasoning_state: "very_confident" })?.reasoning_state).toBeNull();
    expect(sanitizeExplainability({ reasoning_state: 42 })?.reasoning_state).toBeNull();
    expect(sanitizeExplainability({ reasoning_state: null })?.reasoning_state).toBeNull();
  });

  it("P2B-02/P2B-03/P2B-04: keeps operational_assessment/company_brain_alignment/risk_assessment strings verbatim", () => {
    const sanitized = sanitizeExplainability({
      operational_assessment: "Hall 2 production trend is stable.",
      company_brain_alignment: "partially supported",
      risk_assessment: "Moderate risk if trend continues.",
    });
    expect(sanitized?.operational_assessment).toBe("Hall 2 production trend is stable.");
    expect(sanitized?.company_brain_alignment).toBe("partially supported");
    expect(sanitized?.risk_assessment).toBe("Moderate risk if trend continues.");
  });

  it("P2B-09: drops non-string operational_assessment/company_brain_alignment/risk_assessment rather than crashing", () => {
    const sanitized = sanitizeExplainability({
      operational_assessment: { nested: "object" },
      company_brain_alignment: 42,
      risk_assessment: ["not", "a", "string"],
    });
    expect(sanitized?.operational_assessment).toBeNull();
    expect(sanitized?.company_brain_alignment).toBeNull();
    expect(sanitized?.risk_assessment).toBeNull();
  });

  it("P2B-04: keeps tensions/evidence_gaps as arrays of safe strings", () => {
    const sanitized = sanitizeExplainability({
      tensions: ["Evidence suggests X while policy prefers Y."],
      evidence_gaps: ["Water consumption reading missing."],
    });
    expect(sanitized?.tensions).toEqual(["Evidence suggests X while policy prefers Y."]);
    expect(sanitized?.evidence_gaps).toEqual(["Water consumption reading missing."]);
  });

  it("P2B-09: filters non-string entries out of tensions/evidence_gaps rather than crashing", () => {
    const sanitized = sanitizeExplainability({
      tensions: ["safe", 42, { nested: "leak" }, null],
      evidence_gaps: "not-an-array",
    });
    expect(sanitized?.tensions).toEqual(["safe"]);
    expect(sanitized?.evidence_gaps).toEqual([]);
  });

  it("P2B-05: resolves structured missing_evidence through the SAME evidence sanitizer as cited_evidence", () => {
    const sanitized = sanitizeExplainability({
      missing_evidence: [
        {
          id: "m1",
          label: "water_consumption",
          filename: null,
          report_date: null,
          entity: null,
          epistemic_origin: null,
          source_time_status: null,
        },
      ],
    });
    expect(sanitized?.missing_evidence).toEqual([
      {
        id: "m1",
        label: "water_consumption",
        filename: null,
        report_date: null,
        entity: null,
        epistemic_origin: null,
        source_time_status: null,
      },
    ]);
  });

  it("P2B-06/P2B-09: strips unapproved extra fields nested inside a missing_evidence item, drops items missing an id", () => {
    const sanitized = sanitizeExplainability({
      missing_evidence: [
        {
          id: "m1",
          label: "water_consumption",
          source_file_id: "b6e6b8f0-1111-2222-3333-444455556666",
          filesystem_path: "/var/data/hall2.xlsx",
          T_ref: "T3",
        },
        { label: "no id here - dropped" },
      ],
    });
    expect(sanitized?.missing_evidence).toHaveLength(1);
    const serialized = JSON.stringify(sanitized?.missing_evidence);
    expect(serialized).not.toContain("source_file_id");
    expect(serialized).not.toContain("filesystem_path");
    expect(serialized).not.toContain("b6e6b8f0-1111-2222-3333-444455556666");
    expect(serialized).not.toContain("T_ref");
  });

  it("P2B-09: malformed missing_evidence input fails safely without throwing", () => {
    expect(() => sanitizeExplainability({ missing_evidence: "not-an-array" })).not.toThrow();
    expect(sanitizeExplainability({ missing_evidence: "not-an-array" })?.missing_evidence).toEqual([]);
    expect(() => sanitizeExplainability({ missing_evidence: 42 })).not.toThrow();
  });
});
