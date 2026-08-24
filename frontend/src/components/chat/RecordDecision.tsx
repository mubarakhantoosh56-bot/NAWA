"use client";

import { FormEvent, useId, useState } from "react";

import { useLanguage } from "@/components/i18n/LanguageProvider";
import { ApiError } from "@/lib/api/client";
import { recordDecision } from "@/lib/api/decisions";

// M8 Slice 3B-2: inline Record Decision action, styled consistently with
// ExecutiveReasoningPanel (same container conventions, no modal/dialog
// infrastructure - none exists elsewhere in this frontend). Visibility
// (canRecordDecisions + a non-null reasoningReceiptId) is decided by the
// caller (ChatPanel) - this component assumes it is safe to render once
// given a receiptId, and only branches internally on whether THIS turn's
// decision has already been recorded (recordedDecisionId).
//
// Core law: decision_text is always blank by default and never
// auto-populated from the AI's own recommendation/ceo_text - the human
// must explicitly write or paste it themselves before Record Decision can
// be submitted.
type RecordDecisionProps = {
  token: string;
  reasoningReceiptId: string;
  recordedDecisionId: string | null;
  onRecorded: (decisionId: string) => void;
};

export function RecordDecision({ token, reasoningReceiptId, recordedDecisionId, onRecorded }: RecordDecisionProps) {
  const { t } = useLanguage();
  const decisionFieldId = useId();
  const rationaleFieldId = useId();
  const [isOpen, setIsOpen] = useState(false);
  const [decisionText, setDecisionText] = useState("");
  const [rationale, setRationale] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (recordedDecisionId) {
    return (
      <div className="mt-3 inline-flex rounded-md border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
        {t("decisionRecorded")}
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
          {t("recordDecision")}
        </button>
      </div>
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = decisionText.trim();
    if (!trimmed || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await recordDecision(token, {
        reasoning_receipt_id: reasoningReceiptId,
        decision_text: trimmed,
        rationale: rationale.trim() || null,
        situation_id: null,
      });
      onRecorded(response.id);
      setIsOpen(false);
      setDecisionText("");
      setRationale("");
    } catch (caught) {
      setError(mapDecisionError(caught, t));
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleCancel() {
    setIsOpen(false);
    setDecisionText("");
    setRationale("");
    setError(null);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-3 space-y-2 rounded-md border border-line bg-surface p-3"
    >
      <div className="executive-label">{t("recordDecision")}</div>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">{error}</div>
      ) : null}

      <div>
        <label htmlFor={decisionFieldId} className="text-xs font-semibold text-muted">
          {t("decision")}
        </label>
        <textarea
          id={decisionFieldId}
          className="input mt-1 min-h-16 w-full resize-none text-sm leading-6"
          value={decisionText}
          onChange={(event) => setDecisionText(event.target.value)}
          disabled={isSubmitting}
        />
      </div>

      <div>
        <label htmlFor={rationaleFieldId} className="text-xs font-semibold text-muted">
          {t("rationale")}
        </label>
        <textarea
          id={rationaleFieldId}
          className="input mt-1 min-h-12 w-full resize-none text-sm leading-6"
          value={rationale}
          onChange={(event) => setRationale(event.target.value)}
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
          disabled={isSubmitting || !decisionText.trim()}
        >
          {isSubmitting ? t("recordingDecision") : t("recordDecision")}
        </button>
      </div>
    </form>
  );
}

function mapDecisionError(caught: unknown, t: (key: string) => string): string {
  if (caught instanceof ApiError) {
    if (caught.status === 403) {
      return t("recordDecisionPermissionDenied");
    }
    if (caught.status === 404) {
      return t("recordDecisionReceiptUnavailable");
    }
    if (caught.status === 422) {
      return t("recordDecisionInvalid");
    }
  }
  return t("recordDecisionFailed");
}
