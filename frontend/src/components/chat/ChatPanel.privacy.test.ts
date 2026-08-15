import { describe, expect, it } from "vitest";

import {
  buildPersistedTurns,
  parseStoredTurns,
  toPersistedChatResponse,
} from "@/components/chat/ChatPanel";
import type { ChatResponse, ChatTurn } from "@/lib/types";

// M7 Slice 2A privacy contract tests (Section 17, P1-P5, P8). These prove
// the ChatPanel <-> localStorage boundary never leaks internal backend
// material - see ChatPanel.tsx's PersistedChatResponse/toPersistedChatResponse/
// buildPersistedTurns/parseStoredTurns for the implementation this exercises.

// Deliberately over-permissive: the real ChatContext/ChatDecisionContext
// types no longer allow these extra fields at all (that is the point of
// the Slice 2A allowlist types) - this fixture simulates a hypothetical
// backend regression/version mismatch that sends more than the contract
// promises, so the tests below prove toPersistedChatResponse only ever
// COPIES named fields (never spreads/passes through the input object),
// which stays safe even if the runtime payload does not match the type.
function fakeBackendResponse(): ChatResponse {
  const payload = {
    ceo_text: "Hall 2 production is on track.",
    logic_json: {
      reasoning_assessment: {
        reasoning_state: "aligned",
        confidence: 80,
        recommendation_basis: { evidence_basis: ["T1"], company_basis: ["CB1"], missing_evidence: [] },
      },
      internal_debug: "should never be persisted",
    },
    followup_question: "Would you like the weekly trend as well?",
    meta: {
      company_id: "company-123",
      session_id: "session-456",
      language: "en",
      parse_ok: true,
      memory_injected: true,
      events_count: 4,
      context: {
        operational_events_bridge: { status: "ok", fetched: 2, merged: 2, deduplicated: 0 },
        truth_context_bridge: { status: "ok", evidence_count: 3 },
        company_brain_bridge: { status: "ok", dairtna_knowledge_included: true },
        company_intelligence_profile: { company_name: "Jannat Al-Firdaws", industry: "FMCG" },
        decision_context: {
          department: { key: "dairtna_poultry", name: "Dairtna Poultry", scope: "department" },
          operational_events: [{ event_type: "operational.production.issue", summary: "Feed shortage" }],
          // Anything beyond department/operational_events must never reach
          // the persisted shape even though the backend allowlist itself
          // would already have stripped these server-side - this is a
          // defense-in-depth check on the frontend boundary too.
          operational_truth_context: [
            {
              type: "bird_balance",
              status: "available",
              source_file_id: "b6e6b8f0-1111-2222-3333-444455556666",
              source_company_id: "aaaa0000-1111-2222-3333-444455556666",
              source_filename: "hall2_daily_report.xlsx",
            },
          ],
          company_brain_context: [{ type: "POLICY", statement: "Confidential internal doctrine text." }],
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
            },
          ],
          cited_company_basis: [
            { id: "c1", label: "Feed sourcing priority", type: "POLICY", statement: "Prefer local feed suppliers." },
          ],
          confidence: { value: 80, band: "high", drivers: [] },
          // M7 Slice 2B safe executive-provenance fields.
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
            },
          ],
        },
      },
    },
  };
  return payload as unknown as ChatResponse;
}

describe("toPersistedChatResponse", () => {
  it("P1: does not contain the broad meta.context object", () => {
    const persisted = toPersistedChatResponse(fakeBackendResponse());
    expect(persisted).not.toHaveProperty("meta.context");
    // The persisted meta only ever has these four keys.
    expect(Object.keys(persisted.meta).sort()).toEqual(
      ["events_count", "explainability", "memory_injected", "parse_ok"].sort(),
    );
  });

  it("P2: does not contain the raw Decision Context (department/operational_events)", () => {
    const persisted = toPersistedChatResponse(fakeBackendResponse());
    const serialized = JSON.stringify(persisted);
    expect(serialized).not.toContain("decision_context");
    expect(serialized).not.toContain("dairtna_poultry");
    expect(serialized).not.toContain("Feed shortage");
  });

  it("P3: does not contain Truth/Company Brain catalogs", () => {
    const persisted = toPersistedChatResponse(fakeBackendResponse());
    const serialized = JSON.stringify(persisted);
    expect(serialized).not.toContain("operational_truth_context");
    expect(serialized).not.toContain("company_brain_context");
    expect(serialized).not.toContain("Confidential internal doctrine text");
  });

  it("P4: does not contain internal UUID/path provenance beyond the sanitized explainability filename", () => {
    const persisted = toPersistedChatResponse(fakeBackendResponse());
    const serialized = JSON.stringify(persisted);
    expect(serialized).not.toContain("source_file_id");
    expect(serialized).not.toContain("source_company_id");
    expect(serialized).not.toContain("aaaa0000-1111-2222-3333-444455556666");
    // The one filename explainability legitimately carries through is the
    // sanitized, non-UUID, non-path human-readable filename - safe by
    // Section 5's own allowlist (already a public field on the backend).
    expect(serialized).toContain("hall2_daily_report.xlsx");
  });

  it("P5: retains the safe visible answer and explainability data needed for chat continuity", () => {
    const persisted = toPersistedChatResponse(fakeBackendResponse());
    expect(persisted.ceo_text).toBe("Hall 2 production is on track.");
    expect(persisted.followup_question).toBe("Would you like the weekly trend as well?");
    expect(persisted.meta.parse_ok).toBe(true);
    expect(persisted.meta.memory_injected).toBe(true);
    expect(persisted.meta.events_count).toBe(4);
    expect(persisted.meta.explainability?.cited_evidence[0].label).toBe("bird_balance");
    expect(persisted.meta.explainability?.confidence?.band).toBe("high");
  });

  it("P2B-01..05: retains the new Slice 2B safe executive-provenance fields", () => {
    const persisted = toPersistedChatResponse(fakeBackendResponse());
    const explainability = persisted.meta.explainability;
    expect(explainability?.reasoning_state).toBe("aligned");
    expect(explainability?.operational_assessment).toBe("Hall 2 trend reviewed against current evidence.");
    expect(explainability?.company_brain_alignment).toBe("supported by current evidence");
    expect(explainability?.tensions).toEqual([]);
    expect(explainability?.evidence_gaps).toEqual([]);
    expect(explainability?.risk_assessment).toBe("Low risk given current evidence.");
    expect(explainability?.missing_evidence).toEqual([
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

  it("does not carry logic_json at all", () => {
    const persisted = toPersistedChatResponse(fakeBackendResponse());
    expect(persisted).not.toHaveProperty("logic_json");
  });

  it("2A-F2: sanitizes a malformed/over-broad LIVE explainability payload via the runtime sanitizer, not a TypeScript cast", () => {
    const overBroad = fakeBackendResponse();
    // Simulate a live backend response whose explainability object itself
    // carries extra internal fields beyond the approved allowlist (a
    // hypothetical backend regression) - defense in depth on top of the
    // backend's own sanitization.
    (overBroad.meta.context as Record<string, unknown>).explainability = {
      cited_evidence: [
        {
          id: "e1",
          label: "bird_balance",
          filename: "hall2_daily_report.xlsx",
          report_date: "2026-06-01",
          entity: { type: "production_hall", reference: "2", extra_secret: "leak" },
          epistemic_origin: "observed",
          source_time_status: "authoritative",
          source_file_id: "b6e6b8f0-1111-2222-3333-444455556666",
          storage_path: "s3://bucket/hall2.xlsx",
        },
      ],
      cited_company_basis: [],
      confidence: { value: 80, band: "high", drivers: ["missing_evidence", "made_up_driver"], extra_internal: "leak" },
    };

    const persisted = toPersistedChatResponse(overBroad);
    const serialized = JSON.stringify(persisted);
    expect(serialized).not.toContain("extra_secret");
    expect(serialized).not.toContain("source_file_id");
    expect(serialized).not.toContain("b6e6b8f0-1111-2222-3333-444455556666");
    expect(serialized).not.toContain("storage_path");
    expect(serialized).not.toContain("extra_internal");
    expect(serialized).not.toContain("made_up_driver");
    expect(persisted.meta.explainability?.cited_evidence[0].entity).toEqual({
      type: "production_hall",
      reference: "2",
    });
    expect(persisted.meta.explainability?.confidence?.drivers).toEqual(["missing_evidence"]);
  });
});

describe("buildPersistedTurns", () => {
  it("strips logicJson from every turn before it would be written to storage", () => {
    const turns: Record<string, ChatTurn[]> = {
      ceo: [
        {
          id: "t1",
          userMessage: "Status?",
          response: toPersistedChatResponse(fakeBackendResponse()),
          logicJson: { should_never_persist: true },
        },
      ],
    };

    const persisted = buildPersistedTurns(turns);
    const serialized = JSON.stringify(persisted);
    expect(serialized).not.toContain("should_never_persist");
    expect(persisted.ceo[0]).not.toHaveProperty("logicJson");
  });
});

describe("parseStoredTurns (P8: legacy payload safety)", () => {
  it("P8: gracefully drops malformed JSON instead of throwing", () => {
    expect(() => parseStoredTurns("{not valid json")).not.toThrow();
    expect(parseStoredTurns("{not valid json")).toEqual({});
  });

  it("P8: gracefully drops a non-object top-level payload", () => {
    expect(parseStoredTurns("42")).toEqual({});
    expect(parseStoredTurns("null")).toEqual({});
    expect(parseStoredTurns('"a string"')).toEqual({});
  });

  it("P8: gracefully drops entries missing required fields instead of crashing", () => {
    const raw = JSON.stringify({
      ceo: [
        { id: "ok-1", userMessage: "hi", response: { ceo_text: "hello", meta: {} } },
        { id: "missing-response" },
        { userMessage: "no id", response: { ceo_text: "x", meta: {} } },
        "not-an-object",
        null,
      ],
    });

    const parsed = parseStoredTurns(raw);
    expect(parsed.ceo).toHaveLength(1);
    expect(parsed.ceo[0].id).toBe("ok-1");
  });

  it("safely reconstructs a legacy (pre-Slice-2A) payload that has extra internal fields, without re-exposing them", () => {
    const legacyRaw = JSON.stringify({
      ceo: [
        {
          id: "legacy-1",
          userMessage: "old question",
          response: {
            ceo_text: "old answer",
            logic_json: { legacy_internal: "should be ignored, not crash" },
            followup_question: null,
            meta: {
              company_id: "legacy-co",
              session_id: "legacy-session",
              parse_ok: true,
              memory_injected: false,
              events_count: 1,
              context: {
                operational_truth_context: [{ leaked: "legacy internal data" }],
                decision_context: { operational_truth_context: [{ leaked: "should not resurface" }] },
              },
            },
          },
        },
      ],
    });

    const parsed = parseStoredTurns(legacyRaw);
    expect(parsed.ceo).toHaveLength(1);
    const turn = parsed.ceo[0];
    expect(turn.response.ceo_text).toBe("old answer");
    expect(turn).not.toHaveProperty("logicJson");
    const serialized = JSON.stringify(turn);
    expect(serialized).not.toContain("legacy internal data");
    expect(serialized).not.toContain("should not resurface");
    expect(serialized).not.toContain("legacy_internal");
  });

  it("round-trips a freshly persisted turn back into the same sanitized shape", () => {
    const original = toPersistedChatResponse(fakeBackendResponse());
    const stored = buildPersistedTurns({
      ceo: [{ id: "t1", userMessage: "Status?", response: original }],
    });
    const parsed = parseStoredTurns(JSON.stringify(stored));
    expect(parsed.ceo[0].response).toEqual(original);
  });

  it("2A-F2: strips every unapproved field from an adversarial legacy explainability payload (Section 13)", () => {
    const maliciousRaw = JSON.stringify({
      ceo: [
        {
          id: "legacy-1",
          userMessage: "old question",
          response: {
            ceo_text: "old answer",
            followup_question: null,
            meta: {
              parse_ok: true,
              memory_injected: false,
              events_count: 1,
              explainability: {
                cited_evidence: [
                  {
                    id: "e1",
                    label: "bird_balance",
                    filename: "hall2_daily_report.xlsx",
                    report_date: "2026-06-01",
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
                confidence: {
                  value: 80,
                  band: "high",
                  drivers: ["missing_evidence", "made_up_driver"],
                  extra_internal: "leak",
                },
              },
            },
          },
        },
      ],
    });

    const parsed = parseStoredTurns(maliciousRaw);
    expect(parsed.ceo).toHaveLength(1);
    const turn = parsed.ceo[0];

    // Allowed safe values survive.
    expect(turn.response.meta.explainability?.cited_evidence[0].label).toBe("bird_balance");
    expect(turn.response.meta.explainability?.cited_evidence[0].entity).toEqual({
      type: "production_hall",
      reference: "2",
    });
    expect(turn.response.meta.explainability?.confidence?.drivers).toEqual(["missing_evidence"]);

    // Reserialize through the actual persisted shape (as buildPersistedTurns
    // would write it) and prove the unsafe strings still do not appear.
    const reStored = buildPersistedTurns({ ceo: [{ ...turn, logicJson: undefined }] });
    const serialized = JSON.stringify(reStored);
    for (const unsafe of [
      "extra_secret",
      "source_file_id",
      "source_company_id",
      "source_department_id",
      "b6e6b8f0-1111-2222-3333-444455556666",
      "aaaa0000-1111-2222-3333-444455556666",
      "cccc0000-1111-2222-3333-444455556666",
      "filesystem_path",
      "storage_path",
      "secret_extra",
      "provenance_note",
      "extra_internal",
      "made_up_driver",
    ]) {
      expect(serialized).not.toContain(unsafe);
    }
  });

  it("P2B-09: strips malformed/adversarial Slice 2B fields from a legacy payload rather than crashing", () => {
    const maliciousRaw = JSON.stringify({
      ceo: [
        {
          id: "legacy-2b",
          userMessage: "old question",
          response: {
            ceo_text: "old answer",
            followup_question: null,
            meta: {
              parse_ok: true,
              memory_injected: false,
              events_count: 1,
              explainability: {
                cited_evidence: [],
                cited_company_basis: [],
                confidence: null,
                reasoning_state: "an_invented_fifth_state",
                operational_assessment: { nested: "not a string" },
                company_brain_alignment: 12345,
                tensions: ["safe-tension", { nested: "leak" }],
                evidence_gaps: "not-an-array",
                risk_assessment: ["also", "not", "a", "string"],
                missing_evidence: [
                  {
                    id: "m1",
                    label: "water_consumption",
                    source_file_id: "b6e6b8f0-1111-2222-3333-444455556666",
                    filesystem_path: "/var/data/hall2.xlsx",
                    T_ref: "T3",
                  },
                  { label: "no id here - must be dropped" },
                ],
              },
            },
          },
        },
      ],
    });

    const parsed = parseStoredTurns(maliciousRaw);
    expect(parsed.ceo).toHaveLength(1);
    const explainability = parsed.ceo[0].response.meta.explainability;

    expect(explainability?.reasoning_state).toBeNull();
    expect(explainability?.operational_assessment).toBeNull();
    expect(explainability?.company_brain_alignment).toBeNull();
    expect(explainability?.tensions).toEqual(["safe-tension"]);
    expect(explainability?.evidence_gaps).toEqual([]);
    expect(explainability?.risk_assessment).toBeNull();
    expect(explainability?.missing_evidence).toHaveLength(1);

    const serialized = JSON.stringify(explainability);
    expect(serialized).not.toContain("an_invented_fifth_state");
    expect(serialized).not.toContain("source_file_id");
    expect(serialized).not.toContain("filesystem_path");
    expect(serialized).not.toContain("b6e6b8f0-1111-2222-3333-444455556666");
    expect(serialized).not.toContain("T_ref");
  });
});
