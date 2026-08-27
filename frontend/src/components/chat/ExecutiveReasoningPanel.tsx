"use client";

import { useLanguage } from "@/components/i18n/LanguageProvider";
import type {
  CitedOrganizationalMemoryItem,
  ConfidenceDriver,
  Explainability,
  ExplainabilityCompanyBasisItem,
  ExplainabilityConfidence,
  ExplainabilityEvidenceItem,
  OrganizationalMemoryOutcomeExplainability,
  OutcomeResultState,
  ReasoningState,
} from "@/lib/types";

// M7 Slice 2B: renders the FINAL accepted candidate's safe executive-
// provenance fields (meta.context.explainability, sanitized both server-
// and client-side - see app/services/explainability.py and
// lib/chat/storage.ts's sanitizeExplainability). Presentation only: no
// field here is computed, inferred, summarized, or reconstructed - every
// value is a verbatim passthrough of what the backend already resolved
// and validated. The existing ceo_text remains the primary recommendation;
// this panel is supporting executive provenance, never a second competing
// answer. Never reads confidence.value (frozen UX decision, Section 12) -
// only band + deterministic driver translations.
export function ExecutiveReasoningPanel({ explainability }: { explainability: Explainability | null }) {
  const { t } = useLanguage();

  // Section 28: omit the panel entirely when there is insufficient safe
  // reasoning data to render it meaningfully (legacy/pre-Slice-2B
  // responses, demo fixtures with no real reasoning, or any turn where
  // the backend genuinely had nothing to report) - never a fabricated
  // placeholder, never a red error.
  if (!explainability || !explainability.reasoning_state) {
    return null;
  }

  const {
    reasoning_state: reasoningState,
    operational_assessment: operationalAssessment,
    company_brain_alignment: companyBrainAlignment,
    tensions,
    cited_evidence: citedEvidence,
    cited_company_basis: citedCompanyBasis,
    cited_organizational_memory: citedOrganizationalMemory,
    evidence_gaps: evidenceGaps,
    missing_evidence: missingEvidence,
    risk_assessment: riskAssessment,
    confidence,
  } = explainability;

  return (
    <div className="mt-4 space-y-3 rounded-md border border-line bg-surface p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="executive-label">{t("executiveReasoning.title")}</div>
        <ReasoningStateBadge state={reasoningState} />
      </div>

      <p className="text-xs leading-5 text-muted">{reasoningStateHint(reasoningState, t)}</p>

      {operationalAssessment ? (
        <TextSection title={t("executiveReasoning.operationalAssessment")} body={operationalAssessment} />
      ) : null}

      {/* Frozen UX decision (Slice 2B Section 8): rendered VERBATIM from
          the backend controlled vocabulary - never re-mapped/translated. */}
      {companyBrainAlignment ? (
        <TextSection title={t("executiveReasoning.companyBrainAlignment")} body={companyBrainAlignment} />
      ) : null}

      {tensions.length > 0 ? <ListSection title={t("executiveReasoning.tensions")} items={tensions} /> : null}

      <EvidenceListSection
        title={t("executiveReasoning.evidenceUsed")}
        items={citedEvidence}
        empty={t("executiveReasoning.noEvidenceCited")}
        t={t}
      />

      <CompanyBasisListSection
        title={t("executiveReasoning.companyBasisUsed")}
        items={citedCompanyBasis}
        empty={t("executiveReasoning.noCompanyBasisCited")}
      />

      <HistoricalOrganizationalMemorySection items={citedOrganizationalMemory} />

      <MissingEvidenceSection
        title={t("executiveReasoning.missingEvidence")}
        evidenceGaps={evidenceGaps}
        missingEvidence={missingEvidence}
        t={t}
      />

      {riskAssessment ? <TextSection title={t("executiveReasoning.risk")} body={riskAssessment} /> : null}

      {confidence ? <ConfidenceSection confidence={confidence} /> : null}
    </div>
  );
}

function ReasoningStateBadge({ state }: { state: ReasoningState }) {
  const { t } = useLanguage();
  const label =
    state === "aligned"
      ? t("executiveReasoning.stateAligned")
      : state === "tension"
        ? t("executiveReasoning.stateTension")
        : t("executiveReasoning.stateInsufficientEvidence");
  const toneClass =
    state === "aligned"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : state === "tension"
        ? "border-amber-200 bg-amber-50 text-amber-700"
        : "border-slate-300 bg-slate-100 text-slate-700";

  return <span className={`rounded border px-2 py-1 text-xs font-medium ${toneClass}`}>{label}</span>;
}

function reasoningStateHint(state: ReasoningState, t: (key: string) => string): string {
  if (state === "aligned") {
    return t("executiveReasoning.alignedHint");
  }
  if (state === "tension") {
    return t("executiveReasoning.tensionHint");
  }
  return t("executiveReasoning.insufficientEvidenceHint");
}

function TextSection({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs font-semibold uppercase text-muted">{title}</div>
      <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-ink">{body}</p>
    </div>
  );
}

function ListSection({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs font-semibold uppercase text-muted">{title}</div>
      <ul className="mt-2 space-y-1 text-sm leading-6 text-ink">
        {items.map((item, index) => (
          <li key={`${title}-${index}`}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function EvidenceListSection({
  title,
  items,
  empty,
  t,
}: {
  title: string;
  items: ExplainabilityEvidenceItem[];
  empty: string;
  t: (key: string) => string;
}) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs font-semibold uppercase text-muted">{title}</div>
      {items.length > 0 ? (
        <ul className="mt-2 space-y-1.5">
          {items.map((item) => (
            <EvidenceItemRow key={item.id} item={item} t={t} />
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-sm leading-6 text-muted">{empty}</p>
      )}
    </div>
  );
}

function CompanyBasisListSection({
  title,
  items,
  empty,
}: {
  title: string;
  items: ExplainabilityCompanyBasisItem[];
  empty: string;
}) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs font-semibold uppercase text-muted">{title}</div>
      {items.length > 0 ? (
        <ul className="mt-2 space-y-1.5">
          {items.map((item) => (
            <CompanyBasisItemRow key={item.id} item={item} />
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-sm leading-6 text-muted">{empty}</p>
      )}
    </div>
  );
}

// M8 Slice 4C-2: renders the FINAL accepted candidate's
// cited_organizational_memory - a THIRD, distinct citation category,
// never merged with Evidence Used/Company Brain Basis above. Hidden
// entirely when nothing was cited (Step 10): an empty-state sentence here
// risks reading as "NAWA has no historical memory," which the section-
// level copy below explicitly avoids implying. Every value rendered is a
// verbatim passthrough of the already-sanitized public backend/client
// shape - nothing here is computed, inferred, or re-truncated.
function HistoricalOrganizationalMemorySection({ items }: { items: CitedOrganizationalMemoryItem[] }) {
  const { t } = useLanguage();

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs font-semibold uppercase text-muted">{t("executiveReasoning.historicalMemoryTitle")}</div>
      <p className="mt-1 text-xs leading-5 text-muted">{t("executiveReasoning.historicalMemoryDescription")}</p>
      {/* Section-level only (Step 13) - never repeated per Outcome. */}
      <p className="mt-1 text-xs leading-5 text-muted">{t("executiveReasoning.historicalMemoryCausalityDisclaimer")}</p>
      <ul className="mt-2 space-y-2">
        {items.map((item) => (
          // item.id ("h1", "h2", ...) is presentation-only, used ONLY as
          // the React key - never rendered as visible text (Step 14,
          // matches the existing e#/c# convention).
          <OrganizationalMemoryItemRow key={item.id} item={item} t={t} />
        ))}
      </ul>
    </div>
  );
}

function OrganizationalMemoryItemRow({
  item,
  t,
}: {
  item: CitedOrganizationalMemoryItem;
  t: (key: string) => string;
}) {
  return (
    <li className="rounded border border-line bg-surface p-2 text-sm leading-6 text-ink">
      <div className="text-xs font-semibold uppercase text-muted">{t("executiveReasoning.historicalDecision")}</div>
      <p className="mt-0.5 whitespace-pre-wrap">{item.decision}</p>

      {/* Rationale omitted entirely when null - never a fabricated
          "No rationale" placeholder (Step 16). */}
      {item.rationale ? (
        <>
          <div className="mt-2 text-xs font-semibold uppercase text-muted">{t("rationale")}</div>
          <p className="mt-0.5 whitespace-pre-wrap">{item.rationale}</p>
        </>
      ) : null}

      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted">
        <span>
          {t("executiveReasoning.historicalDecisionDate")}: {item.decided_at}
        </span>
      </div>

      {item.outcomes.length > 0 ? (
        <div className="mt-2">
          <div className="text-xs font-semibold uppercase text-muted">
            {t("executiveReasoning.historicalRecordedOutcomes")}
          </div>
          <ul className="mt-1 space-y-1">
            {item.outcomes.map((outcome, index) => (
              <OrganizationalMemoryOutcomeRow key={index} outcome={outcome} t={t} />
            ))}
          </ul>
        </div>
      ) : null}

      {item.omitted_outcomes_count > 0 ? (
        <p className="mt-2 text-xs leading-5 text-muted">
          {item.omitted_outcomes_count} {t("executiveReasoning.historicalOutcomesOmitted")}
        </p>
      ) : null}
    </li>
  );
}

function OrganizationalMemoryOutcomeRow({
  outcome,
  t,
}: {
  outcome: OrganizationalMemoryOutcomeExplainability;
  t: (key: string) => string;
}) {
  return (
    <li className="rounded border border-line bg-white p-2 text-xs leading-5 text-ink">
      <div className="flex flex-wrap items-center gap-2">
        <ResultStateBadge state={outcome.result_state} t={t} />
        <span className="text-muted">
          {t("executiveReasoning.historicalObservedAt")}: {outcome.observed_at}
        </span>
      </div>
      <p className="mt-1 whitespace-pre-wrap">{outcome.summary}</p>
    </li>
  );
}

// Step 19: reuses the SAME top-level keys RecordOutcome.tsx already uses
// for this exact OutcomeResultState enum - never a duplicate translation,
// never a numeric score. `unknown` renders its own distinct label, never
// coerced to "neutral" or omitted (Step 23).
function omResultStateLabel(state: OutcomeResultState, t: (key: string) => string): string {
  if (state === "positive") {
    return t("resultPositive");
  }
  if (state === "negative") {
    return t("resultNegative");
  }
  if (state === "mixed") {
    return t("resultMixed");
  }
  return t("resultUnknown");
}

function ResultStateBadge({ state, t }: { state: OutcomeResultState; t: (key: string) => string }) {
  const toneClass =
    state === "positive"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : state === "negative"
        ? "border-rose-200 bg-rose-50 text-rose-700"
        : state === "mixed"
          ? "border-amber-200 bg-amber-50 text-amber-700"
          : "border-slate-300 bg-slate-100 text-slate-700";
  return <span className={`rounded border px-1.5 py-0.5 text-xs font-medium ${toneClass}`}>{omResultStateLabel(state, t)}</span>;
}

// Section 25: evidence_gaps (prose) and missing_evidence (structured
// provenance) are two DISTINCT concepts, kept as clearly separated
// sub-lists in one visual section - never merged or deduplicated.
function MissingEvidenceSection({
  title,
  evidenceGaps,
  missingEvidence,
  t,
}: {
  title: string;
  evidenceGaps: string[];
  missingEvidence: ExplainabilityEvidenceItem[];
  t: (key: string) => string;
}) {
  if (evidenceGaps.length === 0 && missingEvidence.length === 0) {
    return null;
  }
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs font-semibold uppercase text-muted">{title}</div>
      {evidenceGaps.length > 0 ? (
        <ul className="mt-2 space-y-1 text-sm leading-6 text-ink">
          {evidenceGaps.map((item, index) => (
            <li key={`gap-${index}`}>{item}</li>
          ))}
        </ul>
      ) : null}
      {missingEvidence.length > 0 ? (
        <ul className={`space-y-1.5 ${evidenceGaps.length > 0 ? "mt-3" : "mt-2"}`}>
          {missingEvidence.map((item) => (
            <EvidenceItemRow key={item.id} item={item} t={t} />
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function EvidenceItemRow({ item, t }: { item: ExplainabilityEvidenceItem; t: (key: string) => string }) {
  const entityText = item.entity ? [item.entity.type, item.entity.reference].filter(Boolean).join(": ") : null;
  const originLabel = epistemicOriginLabel(item.epistemic_origin, t);
  const sourceTimeLabel = sourceTimeStatusLabel(item.source_time_status, t);
  return (
    <li className="rounded border border-line bg-surface p-2 text-sm leading-6 text-ink">
      <div className="font-medium">{item.label || item.filename || "—"}</div>
      <div className="mt-0.5 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted">
        {item.filename && item.filename !== item.label ? <span>{item.filename}</span> : null}
        {item.report_date ? <span>{item.report_date}</span> : null}
        {entityText ? (
          <span>
            {t("executiveReasoning.entityLabel")}: {entityText}
          </span>
        ) : null}
        {originLabel ? <span>{originLabel}</span> : null}
        {sourceTimeLabel ? (
          <span className={sourceTimeLabel.unresolved ? "text-amber-700" : undefined}>{sourceTimeLabel.text}</span>
        ) : null}
      </div>
    </li>
  );
}

// M7 Slice 2B Correction Round 1 (H-02): closed-mapping display labels for
// the canonical backend evidence-metadata enums - never raw
// English technical tokens dumped into Arabic UI. Canonical values are
// app/oip/models/operational_record.py's VALID_EPISTEMIC_ORIGINS
// (observed/derived/inferred/recommended) and
// app/oce/models/evidence.py's source_time_status
// (authoritative/unresolved/None). An unrecognized/unexpected value is
// OMITTED rather than rendered raw (Section 18).
const EPISTEMIC_ORIGIN_LABEL_KEYS: Record<string, string> = {
  observed: "executiveReasoning.originObserved",
  derived: "executiveReasoning.originDerived",
  inferred: "executiveReasoning.originInferred",
  recommended: "executiveReasoning.originRecommended",
};

function epistemicOriginLabel(value: string | null, t: (key: string) => string): string | null {
  if (!value) {
    return null;
  }
  const key = EPISTEMIC_ORIGIN_LABEL_KEYS[value];
  return key ? t(key) : null;
}

function sourceTimeStatusLabel(
  value: string | null,
  t: (key: string) => string,
): { text: string; unresolved: boolean } | null {
  if (value === "unresolved") {
    return { text: t("executiveReasoning.unresolvedSourceTime"), unresolved: true };
  }
  if (value === "authoritative") {
    return { text: t("executiveReasoning.sourceTimeAuthoritative"), unresolved: false };
  }
  return null;
}

function CompanyBasisItemRow({ item }: { item: ExplainabilityCompanyBasisItem }) {
  return (
    <li className="rounded border border-line bg-surface p-2 text-sm leading-6 text-ink">
      <div className="font-medium">{item.label || "—"}</div>
      {item.type ? <div className="text-xs text-muted">{item.type}</div> : null}
      {item.statement ? <p className="mt-1 text-sm leading-6 text-ink">{item.statement}</p> : null}
    </li>
  );
}

function ConfidenceSection({ confidence }: { confidence: ExplainabilityConfidence }) {
  const { t } = useLanguage();
  const bandLabel =
    confidence.band === "high"
      ? t("executiveReasoning.confidenceHigh")
      : confidence.band === "moderate"
        ? t("executiveReasoning.confidenceModerate")
        : t("executiveReasoning.confidenceLow");
  const toneClass =
    confidence.band === "high"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : confidence.band === "moderate"
        ? "border-amber-200 bg-amber-50 text-amber-700"
        : "border-slate-300 bg-slate-100 text-slate-700";

  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-semibold uppercase text-muted">{t("executiveReasoning.confidence")}</div>
        {/* Frozen UX decision (Slice 2B Section 12): band only - the
            numeric confidence.value is intentionally never read here. */}
        <span className={`rounded border px-2 py-1 text-xs font-medium ${toneClass}`}>{bandLabel}</span>
      </div>
      {confidence.drivers.length > 0 ? (
        <ul className="mt-2 space-y-1 text-xs leading-5 text-muted">
          {confidence.drivers.map((driver) => (
            <li key={driver}>{driverLabel(driver, t)}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function driverLabel(driver: ConfidenceDriver, t: (key: string) => string): string {
  if (driver === "missing_evidence") {
    return t("executiveReasoning.driverMissingEvidence");
  }
  if (driver === "unresolved_source_time") {
    return t("executiveReasoning.driverUnresolvedSourceTime");
  }
  return t("executiveReasoning.driverConflictedCompanyBasis");
}
