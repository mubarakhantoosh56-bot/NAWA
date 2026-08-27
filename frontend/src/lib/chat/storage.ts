// M7 Slice 2A: single source of truth for the NAWA chat localStorage key
// convention, shared between ChatPanel (reads/writes the sanitized
// per-company chat cache) and AuthProvider (clears it on logout/auth-
// bootstrap-failure - a shared-machine privacy boundary, see
// AuthProvider.tsx's logout() and the stored-token bootstrap effect).
import type {
  CitedOrganizationalMemoryItem,
  ConfidenceBand,
  ConfidenceDriver,
  Explainability,
  ExplainabilityCompanyBasisItem,
  ExplainabilityEntity,
  ExplainabilityEvidenceItem,
  OrganizationalMemoryOutcomeExplainability,
  OutcomeResultState,
  ReasoningState,
} from "@/lib/types";

const CHAT_STORAGE_PREFIX = "nawa.chat.";

export function chatStorageKey(companyId: string): string {
  return `${CHAT_STORAGE_PREFIX}${companyId}`;
}

export function clearStoredChat(companyId: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(chatStorageKey(companyId));
}

// Correction Round 1 (2A-F3): used when the authenticated identity cannot
// be trusted (auth-bootstrap failure) - clears EVERY nawa.chat.* cache,
// not just one company's, since we have no trusted company_id to scope to
// at that point. Never touches keys outside the exact `nawa.chat.` prefix
// (e.g. a hypothetical `nawa.chatting.preference` or `nawa.preference`
// must survive). Collects matching keys before removing any of them -
// localStorage.key(i) indices shift if you remove while iterating.
export function clearAllStoredChats(): void {
  if (typeof window === "undefined") {
    return;
  }
  const keysToRemove: string[] = [];
  for (let index = 0; index < window.localStorage.length; index += 1) {
    const key = window.localStorage.key(index);
    if (key && key.startsWith(CHAT_STORAGE_PREFIX)) {
      keysToRemove.push(key);
    }
  }
  keysToRemove.forEach((key) => window.localStorage.removeItem(key));
}

const CONFIDENCE_BANDS: readonly ConfidenceBand[] = ["low", "moderate", "high"];
const CONFIDENCE_DRIVERS: readonly ConfidenceDriver[] = [
  "missing_evidence",
  "unresolved_source_time",
  "conflicted_company_basis",
];
// M7 Slice 2B: the SAME closed enum M6 validates backend-side - never a
// fourth value, never coerced from an unrecognized string.
const REASONING_STATES: readonly ReasoningState[] = ["aligned", "tension", "insufficient_evidence"];
// M8 Slice 4C-2: the SAME closed enum the backend/OutcomeResponse already
// validates (Slice 3C-2) - never a fifth value, never coerced.
const OUTCOME_RESULT_STATES: readonly OutcomeResultState[] = ["positive", "negative", "mixed", "unknown"];

function asNullableString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function sanitizeEntity(value: unknown): ExplainabilityEntity | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const record = value as Record<string, unknown>;
  return {
    type: asNullableString(record.type),
    reference: asNullableString(record.reference),
  };
}

function sanitizeEvidenceItem(value: unknown): ExplainabilityEvidenceItem | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const record = value as Record<string, unknown>;
  if (typeof record.id !== "string") {
    return null;
  }
  return {
    id: record.id,
    label: asNullableString(record.label),
    filename: asNullableString(record.filename),
    report_date: asNullableString(record.report_date),
    entity: sanitizeEntity(record.entity),
    epistemic_origin: asNullableString(record.epistemic_origin),
    source_time_status: asNullableString(record.source_time_status),
  };
}

function sanitizeCompanyBasisItem(value: unknown): ExplainabilityCompanyBasisItem | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const record = value as Record<string, unknown>;
  if (typeof record.id !== "string") {
    return null;
  }
  return {
    id: record.id,
    label: asNullableString(record.label),
    type: asNullableString(record.type),
    statement: asNullableString(record.statement),
  };
}

function sanitizeReasoningState(value: unknown): ReasoningState | null {
  return typeof value === "string" && REASONING_STATES.includes(value as ReasoningState)
    ? (value as ReasoningState)
    : null;
}

function sanitizeStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function sanitizeConfidence(value: unknown): Explainability["confidence"] {
  if (!value || typeof value !== "object") {
    return null;
  }
  const record = value as Record<string, unknown>;
  if (typeof record.value !== "number") {
    return null;
  }
  if (!CONFIDENCE_BANDS.includes(record.band as ConfidenceBand)) {
    return null;
  }
  const drivers = Array.isArray(record.drivers)
    ? record.drivers.filter((driver): driver is ConfidenceDriver =>
        CONFIDENCE_DRIVERS.includes(driver as ConfidenceDriver),
      )
    : [];
  return {
    value: record.value,
    band: record.band as ConfidenceBand,
    drivers,
  };
}

// M8 Slice 4C-2 fix round: shared non-blank-string check for the required
// free-text OM fields (decision/decided_at/summary/observed_at) - `.trim()`
// is used ONLY to detect blank content, never to mutate the value actually
// returned (see the return statements below, which preserve the original
// string verbatim).
function isNonBlankString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

// M8 Slice 4C-2 fix round (Codex blocker): the closed backend contract
// exposes ONLY response-local "h1"/"h2"/... presentation ids - never OM#,
// never a durable UUID, never an arbitrary string. A corrupted/malicious
// persisted payload must not be able to smuggle an internal-looking id
// through as if it were a safe public presentation id.
const ORGANIZATIONAL_MEMORY_PRESENTATION_ID_PATTERN = /^h[1-9][0-9]*$/;

function sanitizeOrganizationalMemoryOutcome(value: unknown): OrganizationalMemoryOutcomeExplainability | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const record = value as Record<string, unknown>;
  if (!OUTCOME_RESULT_STATES.includes(record.result_state as OutcomeResultState)) {
    return null;
  }
  if (!isNonBlankString(record.summary)) {
    return null;
  }
  if (!isNonBlankString(record.observed_at)) {
    return null;
  }
  return {
    result_state: record.result_state as OutcomeResultState,
    summary: record.summary,
    observed_at: record.observed_at,
  };
}

// M8 Slice 4C-2 (Founder Correction: frontend sanitizer must also be
// atomic): mirrors the backend's own public-truthfulness invariant
// (app/services/explainability.py's _sanitize_organizational_memory_item) -
// omitted_outcomes_count means ONLY outcomes omitted from the AI context
// for budgeting, never outcomes hidden by this sanitizer. If the frontend
// dropped only a malformed Outcome while keeping siblings and the stored
// omitted_outcomes_count, a corrupted/legacy localStorage payload could
// reload as "4 shown, omitted_outcomes_count=3" when the original safe
// item had 5 - the same misleading-math risk the backend fix round closed.
// So ANY malformed nested Outcome drops the WHOLE parent OM item here too -
// never a partial outcomes array. This is a client-side shape-integrity
// law (defending against corrupted/legacy persisted data), not new backend
// public-safety logic - a live response's items are already atomic-safe
// before this sanitizer ever runs.
function sanitizeCitedOrganizationalMemoryItem(value: unknown): CitedOrganizationalMemoryItem | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const record = value as Record<string, unknown>;
  if (typeof record.id !== "string" || !ORGANIZATIONAL_MEMORY_PRESENTATION_ID_PATTERN.test(record.id)) {
    return null;
  }
  if (!isNonBlankString(record.decision)) {
    return null;
  }
  if (!isNonBlankString(record.decided_at)) {
    return null;
  }
  if (typeof record.omitted_outcomes_count !== "number" || !Number.isInteger(record.omitted_outcomes_count) || record.omitted_outcomes_count < 0) {
    return null;
  }
  // M8 Slice 4C-2 fix round (Codex blocker): the live public contract is
  // outcome-backed - a Decision-only OM item (empty or malformed outcomes)
  // must never survive sanitization, whether via a missing array, an
  // empty array, or every nested Outcome failing.
  if (!Array.isArray(record.outcomes) || record.outcomes.length === 0) {
    return null;
  }

  const sanitizedOutcomes: OrganizationalMemoryOutcomeExplainability[] = [];
  for (const outcome of record.outcomes) {
    const sanitized = sanitizeOrganizationalMemoryOutcome(outcome);
    if (sanitized === null) {
      return null;
    }
    sanitizedOutcomes.push(sanitized);
  }
  if (sanitizedOutcomes.length === 0) {
    return null;
  }

  return {
    id: record.id,
    decision: record.decision,
    rationale: asNullableString(record.rationale),
    decided_at: record.decided_at,
    outcomes: sanitizedOutcomes,
    omitted_outcomes_count: record.omitted_outcomes_count,
  };
}

// M7 Slice 2A Correction Round 1 (2A-F2): the ONE runtime sanitizer for
// the public explainability shape - the only place an explainability
// value is trusted, whether it came from a live backend ChatResponse
// (toPersistedChatResponse) or a reconstructed localStorage payload,
// current or legacy (toStoredChatTurn). Rebuilds an explicit allowlisted
// object field-by-field, never a TypeScript cast, so a malformed,
// malicious, or over-broad input (extra internal fields nested inside an
// otherwise-valid-looking evidence/company-basis item, an unapproved
// confidence driver string, ...) can never carry those extra properties
// into React state or back out into localStorage. A malformed optional
// item/field is dropped rather than crashing the UI - never throws.
export function sanitizeExplainability(value: unknown): Explainability | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const record = value as Record<string, unknown>;

  const citedEvidence = Array.isArray(record.cited_evidence)
    ? record.cited_evidence
        .map(sanitizeEvidenceItem)
        .filter((item): item is ExplainabilityEvidenceItem => item !== null)
    : [];

  const citedCompanyBasis = Array.isArray(record.cited_company_basis)
    ? record.cited_company_basis
        .map(sanitizeCompanyBasisItem)
        .filter((item): item is ExplainabilityCompanyBasisItem => item !== null)
    : [];

  // M7 Slice 2B: same shape/sanitizer as cited_evidence (backend reuses
  // _sanitize_evidence_item for missing_evidence too - see
  // app/services/explainability.py's _resolve_missing_evidence).
  const missingEvidence = Array.isArray(record.missing_evidence)
    ? record.missing_evidence
        .map(sanitizeEvidenceItem)
        .filter((item): item is ExplainabilityEvidenceItem => item !== null)
    : [];

  // M8 Slice 4C-2: missing/non-array -> [] (also covers legacy persisted
  // explainability written before this slice, keeping reload backward-
  // compatible). Each item sanitized independently; a malformed OM item is
  // dropped while valid sibling OM items survive (unlike a malformed
  // nested Outcome, which drops its own whole parent item - see
  // sanitizeCitedOrganizationalMemoryItem).
  const citedOrganizationalMemory = Array.isArray(record.cited_organizational_memory)
    ? record.cited_organizational_memory
        .map(sanitizeCitedOrganizationalMemoryItem)
        .filter((item): item is CitedOrganizationalMemoryItem => item !== null)
    : [];

  return {
    cited_evidence: citedEvidence,
    cited_company_basis: citedCompanyBasis,
    cited_organizational_memory: citedOrganizationalMemory,
    confidence: sanitizeConfidence(record.confidence),
    reasoning_state: sanitizeReasoningState(record.reasoning_state),
    operational_assessment: asNullableString(record.operational_assessment),
    company_brain_alignment: asNullableString(record.company_brain_alignment),
    tensions: sanitizeStringList(record.tensions),
    evidence_gaps: sanitizeStringList(record.evidence_gaps),
    risk_assessment: asNullableString(record.risk_assessment),
    missing_evidence: missingEvidence,
  };
}
