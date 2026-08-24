"use client";

import { FormEvent, useId, useState } from "react";

import { useLanguage } from "@/components/i18n/LanguageProvider";
import { ApiError } from "@/lib/api/client";
import { recordOutcome } from "@/lib/api/outcomes";
import type { OutcomeCreateRequest, OutcomeResultState } from "@/lib/types";

// M8 Slice 3C-2: inline Record Outcome action, styled consistently with
// RecordDecision (same container conventions, no modal/dialog
// infrastructure - none exists elsewhere in this frontend). Visibility
// (canRecordDecisions + a non-null recorded_decision_id) is decided by the
// caller (ChatPanel) - this component assumes it is safe to render once
// given a decisionMemoryId.
//
// Core law: outcome_summary is always blank by default and never
// auto-populated from the AI's own text/recommendation, and result_state
// is never defaulted or inferred - the human must explicitly write the
// summary and explicitly select a result before Record Outcome can be
// submitted.
//
// Founder Correction (M8 Slice 3C-2): the backend intentionally allows
// multiple active OutcomeMemory rows per decision, and there is no GET/list
// Outcome API. Outcome success state is therefore TRANSIENT COMPONENT-LOCAL
// UI STATE ONLY - no outcome id, summary, result_state, or observed_at is
// ever reported back to a parent or persisted (no onRecorded callback
// exists here, unlike RecordDecision). After a page reload, this component
// has no memory of any prior outcome and simply starts collapsed again -
// Record Outcome remains available for as long as recorded_decision_id
// exists, with no claim about total or final server-side Outcome history.
type RecordOutcomeProps = {
  token: string;
  decisionMemoryId: string;
};

const RESULT_STATES: OutcomeResultState[] = ["positive", "negative", "mixed", "unknown"];

export function RecordOutcome({ token, decisionMemoryId }: RecordOutcomeProps) {
  const { t } = useLanguage();
  const summaryFieldId = useId();
  const observedAtFieldId = useId();
  const [isOpen, setIsOpen] = useState(false);
  const [outcomeSummary, setOutcomeSummary] = useState("");
  const [resultState, setResultState] = useState<OutcomeResultState | null>(null);
  const [observedAt, setObservedAt] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasRecordedOutcome, setHasRecordedOutcome] = useState(false);

  function resetFields() {
    setOutcomeSummary("");
    setResultState(null);
    setObservedAt("");
    setError(null);
  }

  function openFreshForm() {
    resetFields();
    setHasRecordedOutcome(false);
    setIsOpen(true);
  }

  if (hasRecordedOutcome && !isOpen) {
    return (
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <div className="inline-flex rounded-md border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
          {t("outcomeRecorded")}
        </div>
        <button
          type="button"
          className="rounded-md border border-line bg-white px-3 py-1.5 text-xs font-semibold text-ink transition hover:border-accent hover:bg-blue-50"
          onClick={openFreshForm}
        >
          {t("recordAnotherOutcome")}
        </button>
      </div>
    );
  }

  if (!isOpen) {
    return (
      <div className="mt-3">
        <button
          type="button"
          className="rounded-md border border-line bg-white px-3 py-1.5 text-xs font-semibold text-ink transition hover:border-accent hover:bg-blue-50"
          onClick={() => setIsOpen(true)}
        >
          {t("recordOutcome")}
        </button>
      </div>
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedSummary = outcomeSummary.trim();
    if (!trimmedSummary || !resultState || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const trimmedObservedAt = observedAt.trim();
      const payload: OutcomeCreateRequest = {
        decision_memory_id: decisionMemoryId,
        outcome_summary: trimmedSummary,
        result_state: resultState,
        ...(trimmedObservedAt ? { observed_at: new Date(trimmedObservedAt).toISOString() } : {}),
      };
      await recordOutcome(token, payload);
      resetFields();
      setIsOpen(false);
      setHasRecordedOutcome(true);
    } catch (caught) {
      setError(mapOutcomeError(caught, t));
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleCancel() {
    setIsOpen(false);
    resetFields();
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-3 space-y-2 rounded-md border border-line bg-surface p-3"
    >
      <div className="executive-label">{t("recordOutcome")}</div>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">{error}</div>
      ) : null}

      <div>
        <label htmlFor={summaryFieldId} className="text-xs font-semibold text-muted">
          {t("outcomeSummary")}
        </label>
        <textarea
          id={summaryFieldId}
          className="input mt-1 min-h-16 w-full resize-none text-sm leading-6"
          value={outcomeSummary}
          onChange={(event) => setOutcomeSummary(event.target.value)}
          disabled={isSubmitting}
        />
      </div>

      <div>
        <div className="text-xs font-semibold text-muted">{t("result")}</div>
        <div className="mt-1 flex flex-wrap gap-1.5" role="group" aria-label={t("result")}>
          {RESULT_STATES.map((option) => (
            <button
              key={option}
              type="button"
              aria-pressed={resultState === option}
              className={`rounded-md border px-2.5 py-1 text-xs font-semibold transition ${
                resultState === option
                  ? "border-accent bg-accent/10 text-accent"
                  : "border-line bg-white text-ink hover:border-accent hover:bg-blue-50"
              }`}
              onClick={() => setResultState(option)}
              disabled={isSubmitting}
            >
              {resultStateLabel(option, t)}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label htmlFor={observedAtFieldId} className="text-xs font-semibold text-muted">
          {t("observedAt")}
        </label>
        <input
          id={observedAtFieldId}
          type="datetime-local"
          className="input mt-1 w-full text-sm leading-6"
          value={observedAt}
          onChange={(event) => setObservedAt(event.target.value)}
          max={nowLocalDateTimeValue()}
          disabled={isSubmitting}
        />
      </div>

      <div className="flex justify-end gap-2">
        <button
          type="button"
          className="rounded-md border border-line bg-white px-3 py-1.5 text-xs font-semibold text-ink"
          onClick={handleCancel}
          disabled={isSubmitting}
        >
          {t("cancel")}
        </button>
        <button
          type="submit"
          className="button-primary px-3 py-1.5 text-xs"
          disabled={isSubmitting || !outcomeSummary.trim() || !resultState}
        >
          {isSubmitting ? t("recordingOutcome") : t("recordOutcome")}
        </button>
      </div>
    </form>
  );
}

function resultStateLabel(state: OutcomeResultState, t: (key: string) => string): string {
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

function nowLocalDateTimeValue(): string {
  const now = new Date();
  const offsetMs = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offsetMs).toISOString().slice(0, 16);
}

function mapOutcomeError(caught: unknown, t: (key: string) => string): string {
  if (caught instanceof ApiError) {
    if (caught.status === 403) {
      return t("recordOutcomePermissionDenied");
    }
    if (caught.status === 404) {
      return t("recordOutcomeDecisionUnavailable");
    }
    if (caught.status === 422) {
      return t("recordOutcomeInvalid");
    }
  }
  return t("recordOutcomeFailed");
}
