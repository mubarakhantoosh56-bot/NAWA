// M7 Slice 2A: single source of truth for the NAWA chat localStorage key
// convention, shared between ChatPanel (reads/writes the sanitized
// per-company chat cache) and AuthProvider (clears it on logout/auth-
// bootstrap-failure - a shared-machine privacy boundary, see
// AuthProvider.tsx's logout() and the stored-token bootstrap effect).
import type {
  ConfidenceBand,
  ConfidenceDriver,
  Explainability,
  ExplainabilityCompanyBasisItem,
  ExplainabilityEntity,
  ExplainabilityEvidenceItem,
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

  return {
    cited_evidence: citedEvidence,
    cited_company_basis: citedCompanyBasis,
    confidence: sanitizeConfidence(record.confidence),
  };
}
