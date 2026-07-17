"use client";

import { FormEvent, useMemo, useState } from "react";

import { useLanguage } from "@/components/i18n/LanguageProvider";
import { ApiError } from "@/lib/api/client";
import { uploadFile } from "@/lib/api/files";
import { submitOperationalInput } from "@/lib/api/operational-inputs";
import type { CompanyFile, Department, OperationalInputResponse } from "@/lib/types";

type CompanyInputsPanelProps = {
  token: string;
  department: Department | null;
  departments: Department[];
  canSubmit: boolean;
  canUpload: boolean;
  canAssignDepartment: boolean;
  onCaptured?: () => void;
};

type InputMode = "file" | "text";
type RuntimeState = "idle" | "processing" | "waiting_confirmation" | "waiting_evidence" | "completed" | "failed";

type RuntimeResult = {
  sourceLabel: string;
  classification: string;
  department: string;
  pipeline: string;
  confidence: string;
  confidenceReason: string | null;
  runtimeStatus: RuntimeState;
  missingEvidence: string[];
  ceoBrief: CEOBriefPresentation | null;
};

type ExecutiveActionPresentation = {
  action: string;
  // Priority is Business Logic, not Executive Language — null means no
  // priority-assignment rule has been approved yet. Never the
  // pending_executive_language sentinel; render distinctly from it.
  priority: string | null;
  reason: unknown;
  expectedOutcome: unknown;
  owner: string;
  evidenceRefs: string[];
};

type BusinessImpactPresentation = {
  operational: string;
  financial: string;
  strategic: unknown;
};

type ExecutivePriorityPresentation = {
  attentionLevel: unknown;
  situation: unknown;
  businessRisk: unknown;
  executiveTrigger: unknown;
};

type ExecutiveAssessmentPresentation = {
  executiveInterpretation: unknown;
  businessMeaning: unknown;
  executiveRecommendationContext: unknown;
};

type ExecutiveAttentionPresentation = {
  immediate: string[];
  monitor: string[];
};

type CEOBriefPresentation = {
  briefId: string;
  headline: string;
  executivePriority: ExecutivePriorityPresentation | null;
  executiveSummary: string;
  whatChanged: string[];
  facts: string[];
  executiveAssessment: ExecutiveAssessmentPresentation | null;
  businessImpact: string;
  businessImpactDetail: BusinessImpactPresentation | null;
  executiveActions: ExecutiveActionPresentation[];
  recommendedActions: string[];
  confidenceLevel: string;
  confidencePercentage: string | null;
  confidenceExplanation: string;
  missingEvidence: string[];
  recommendedCompanyInputs: string[];
  executiveAttention: ExecutiveAttentionPresentation | null;
};

export function CompanyInputsPanel({
  token,
  department,
  departments,
  canSubmit,
  canUpload,
  canAssignDepartment,
  onCaptured,
}: CompanyInputsPanelProps) {
  const { language, t } = useLanguage();
  const [mode, setMode] = useState<InputMode>("file");
  const [selectedDepartmentId, setSelectedDepartmentId] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [status, setStatus] = useState<RuntimeState>("idle");
  const [errorDetail, setErrorDetail] = useState("");
  const [result, setResult] = useState<RuntimeResult | null>(null);

  const targetDepartmentId = canAssignDepartment ? selectedDepartmentId || null : department?.id ?? null;
  const selectedDepartment = useMemo(
    () => departments.find((item) => item.id === targetDepartmentId) ?? department,
    [department, departments, targetDepartmentId],
  );
  const disabled = status === "processing" || !token;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorDetail("");
    setResult(null);

    if (mode === "file") {
      await submitFile();
      return;
    }

    await submitText();
  }

  async function submitFile() {
    if (!selectedFile || !canUpload || disabled) {
      return;
    }

    setStatus("processing");
    try {
      const uploaded = await uploadFile(token, selectedFile, targetDepartmentId);
      const nextResult = resultFromFile(uploaded, selectedDepartment, language, t);
      setResult(nextResult);
      setStatus(nextResult.runtimeStatus);
      setSelectedFile(null);
      onCaptured?.();
    } catch (caught) {
      setErrorDetail(caught instanceof ApiError ? caught.detail : t("companyInputs.failedDetail"));
      setStatus("failed");
    }
  }

  async function submitText() {
    const cleaned = text.trim();
    if (!cleaned || !canSubmit || disabled) {
      return;
    }

    setStatus("processing");
    try {
      const response = await submitOperationalInput(token, {
        department_id: department?.id ?? null,
        department_type: department?.department_type ?? null,
        target_department_id: canAssignDepartment ? selectedDepartmentId || null : null,
        target_department_type: canAssignDepartment ? selectedDepartment?.department_type ?? null : null,
        category: "daily_update",
        priority: "normal",
        event_date: new Date().toISOString().slice(0, 10),
        text: cleaned,
        metrics: {},
        files_attached: [],
        payload: {
          intake_mode: "company_input_text",
        },
      });
      const nextResult = resultFromText(response, selectedDepartment, language, t);
      setResult(nextResult);
      setStatus(nextResult.runtimeStatus);
      setText("");
      onCaptured?.();
    } catch (caught) {
      setErrorDetail(caught instanceof ApiError ? caught.detail : t("companyInputs.failedDetail"));
      setStatus("failed");
    }
  }

  const canSend =
    mode === "file"
      ? Boolean(selectedFile && canUpload && !disabled)
      : Boolean(text.trim() && canSubmit && !disabled);

  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-line bg-white px-4 py-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="executive-label">{t("companyInputs.label")}</div>
            <h2 className="mt-1 text-lg font-semibold text-ink">{t("companyInputs.title")}</h2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-muted">{t("companyInputs.subtitle")}</p>
          </div>
          <span className="w-fit rounded-md border border-line bg-surface px-2.5 py-1.5 text-xs text-muted">
            {selectedDepartment ? localizeDepartmentName(selectedDepartment.name, language) : t("companyWideScope")}
          </span>
        </div>
      </div>

      <form className="space-y-4 p-4" onSubmit={handleSubmit}>
        <div className="grid gap-3 md:grid-cols-[220px_minmax(0,1fr)]">
          <div className="rounded-md border border-line bg-surface p-1">
            <button
              className={`w-1/2 rounded px-3 py-2 text-sm font-medium transition ${
                mode === "file" ? "bg-white text-ink shadow-sm" : "text-muted hover:text-ink"
              }`}
              type="button"
              onClick={() => setMode("file")}
            >
              {t("companyInputs.file")}
            </button>
            <button
              className={`w-1/2 rounded px-3 py-2 text-sm font-medium transition ${
                mode === "text" ? "bg-white text-ink shadow-sm" : "text-muted hover:text-ink"
              }`}
              type="button"
              onClick={() => setMode("text")}
            >
              {t("companyInputs.text")}
            </button>
          </div>

          <label className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">{t("companyInputs.department")}</span>
            <select
              className="input"
              disabled={disabled || !canAssignDepartment}
              value={canAssignDepartment ? selectedDepartmentId : department?.id ?? ""}
              onChange={(event) => setSelectedDepartmentId(event.target.value)}
            >
              <option value="">{t("companyWideScope")}</option>
              {departments.map((item) => (
                <option key={item.id} value={item.id}>
                  {localizeDepartmentName(item.name, language)}
                </option>
              ))}
            </select>
          </label>
        </div>

        {mode === "file" ? (
          <label className="flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-slate-300 bg-surface px-4 py-8 text-center transition hover:border-accent/50 hover:bg-white">
            <span className="text-sm font-semibold text-ink">
              {selectedFile ? selectedFile.name : t("companyInputs.fileDropTitle")}
            </span>
            <span className="mt-2 text-sm text-muted">{t("companyInputs.fileDropHint")}</span>
            <input
              className="sr-only"
              type="file"
              accept=".xlsx,.xls,.pdf"
              disabled={disabled || !canUpload}
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
          </label>
        ) : (
          <label className="block space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">{t("companyInputs.updateLabel")}</span>
            <textarea
              className="input min-h-40 resize-none leading-6"
              disabled={disabled || !canSubmit}
              placeholder={t("companyInputs.updatePlaceholder")}
              value={text}
              onChange={(event) => setText(event.target.value)}
            />
          </label>
        )}

        <div className="flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-muted">
            {status === "processing"
              ? t("companyInputs.processing")
              : status === "failed"
                ? errorDetail || t("companyInputs.failedDetail")
                : t("companyInputs.readyHint")}
          </div>
          <button className="button-primary sm:w-40" type="submit" disabled={!canSend}>
            {status === "processing" ? t("companyInputs.processingAction") : t("companyInputs.submit")}
          </button>
        </div>
      </form>

      <RuntimeResultPanel status={status} result={result} />
    </section>
  );
}

function RuntimeResultPanel({ status, result }: { status: RuntimeState; result: RuntimeResult | null }) {
  const { t } = useLanguage();

  if (status === "idle") {
    return null;
  }

  if (status === "processing") {
    return (
      <div className="border-t border-line bg-surface px-4 py-4">
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          {t("companyInputs.processing")}
        </div>
      </div>
    );
  }

  if (status === "failed" && !result) {
    return null;
  }

  if (!result) {
    return null;
  }

  return (
    <div className="border-t border-line bg-surface p-4">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <ResultField label={t("companyInputs.classification")} value={result.classification} />
        <ResultField label={t("companyInputs.detectedDepartment")} value={result.department} />
        <ResultField label={t("companyInputs.detectedPipeline")} value={result.pipeline} />
        <ResultField label={t("companyInputs.confidence")} value={result.confidence} />
      </div>

      <div className="mt-4 rounded-md border border-line bg-white p-3">
        <div className="text-xs font-semibold uppercase text-muted">{t("companyInputs.runtimeStatus")}</div>
        <div className="mt-1 text-sm font-medium text-ink">{statusLabel(result.runtimeStatus, t)}</div>
      </div>

      {result.confidenceReason ? (
        <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3">
          <div className="text-xs font-semibold uppercase text-amber-800">{t("companyInputs.confidenceReason")}</div>
          <p className="mt-1 text-sm leading-6 text-amber-900">{result.confidenceReason}</p>
        </div>
      ) : null}

      {result.missingEvidence.length > 0 ? (
        <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3">
          <div className="text-xs font-semibold uppercase text-amber-800">{t("companyInputs.missingEvidence")}</div>
          <ul className="mt-2 space-y-1 text-sm text-amber-900">
            {result.missingEvidence.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {result.ceoBrief ? (
        <CEOBriefPanel brief={result.ceoBrief} />
      ) : null}
    </div>
  );
}

function CEOBriefPanel({ brief }: { brief: CEOBriefPresentation }) {
  const { t } = useLanguage();
  const confidence = brief.confidencePercentage
    ? `${brief.confidenceLevel} (${brief.confidencePercentage})`
    : brief.confidenceLevel;
  const confidenceBody = brief.confidenceExplanation
    ? `${confidence} — ${brief.confidenceExplanation}`
    : confidence;

  return (
    <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase text-emerald-800">{t("companyInputs.ceoBrief")}</div>
          <h3 className="mt-1 text-sm font-semibold text-emerald-950">{brief.headline}</h3>
        </div>
        <span className="w-fit rounded border border-emerald-200 bg-white px-2 py-1 text-xs font-medium text-emerald-900">
          {t("companyInputs.briefId")}: {brief.briefId}
        </span>
      </div>

      {/* PDS-001 §4/§5 Executive Decision Brief structure, in authoritative order. */}
      <div className="mt-3 grid gap-3 lg:grid-cols-2">
        <StructuredBriefSection
          title={t("companyInputs.executivePriority")}
          fields={executivePriorityFields(brief.executivePriority, t)}
        />
        <BriefSection title={t("companyInputs.executiveSummary")} body={brief.executiveSummary} />
        <BriefSection title={t("companyInputs.whatChanged")} items={brief.whatChanged} empty={t("companyInputs.noWhatChanged")} />
        <BriefSection title={t("companyInputs.factsTruthLayer")} items={brief.facts} empty={t("companyInputs.noFacts")} />
        <StructuredBriefSection
          title={t("companyInputs.executiveAssessment")}
          fields={executiveAssessmentFields(brief.executiveAssessment, t)}
        />
        <BusinessImpactSection detail={brief.businessImpactDetail} legacyBody={brief.businessImpact} />
        <ExecutiveActionsSection actions={brief.executiveActions} legacyItems={brief.recommendedActions} />
        <BriefSection title={t("companyInputs.confidenceLevel")} body={confidenceBody} />
        <BriefSection title={t("companyInputs.missingEvidence")} items={brief.missingEvidence} empty={t("companyInputs.noMissingEvidence")} />
        <BriefSection
          title={t("companyInputs.recommendedCompanyInputs")}
          items={brief.recommendedCompanyInputs}
          empty={t("companyInputs.noRecommendedCompanyInputs")}
        />
        <ExecutiveAttentionSection attention={brief.executiveAttention} />
      </div>
    </div>
  );
}

function pendingNote(value: unknown): string | null {
  // Hotfix: some fields (e.g. executive_actions[i].reason/expected_outcome)
  // carry the sentinel as a bare string rather than {status, note} — never
  // let the raw literal reach an executive-facing screen.
  if (value === "pending_executive_language") {
    return "";
  }
  const record = asRecord(value);
  return record.status === "pending_executive_language" ? String(record.note || "") : null;
}

function PendingOrText({ value }: { value: unknown }) {
  const { t } = useLanguage();
  const note = pendingNote(value);
  if (note !== null) {
    return <span className="italic text-amber-700">{t("companyInputs.pendingExecutiveLanguage")}</span>;
  }
  return <>{typeof value === "string" ? value : ""}</>;
}

// Priority is Business Logic, not Executive Language (Founder decision,
// Executive Language Completion) — rendered distinctly from the amber
// "Pending executive language" treatment used by PendingOrText.
function PriorityValue({ value }: { value: string | null }) {
  const { t } = useLanguage();
  if (value === null) {
    return <span className="text-emerald-700/70">{t("companyInputs.priorityNotYetDetermined")}</span>;
  }
  return <>{value}</>;
}

type StructuredField = { label: string; value: unknown };

// Renders a title plus a list of independently-resolved sub-fields, each of
// which may be pending, completed, or (across the whole section) a mix of
// both — unlike the single-value PendingSection it replaces.
function StructuredBriefSection({ title, fields }: { title: string; fields: StructuredField[] }) {
  return (
    <div className="rounded-md border border-emerald-100 bg-white p-3">
      <div className="text-xs font-semibold uppercase text-emerald-800">{title}</div>
      <div className="mt-2 space-y-2 text-sm leading-6 text-emerald-950">
        {fields.map((field) => (
          <div key={field.label}>
            <span className="font-semibold">{field.label}: </span>
            <PendingOrText value={field.value} />
          </div>
        ))}
      </div>
    </div>
  );
}

function executivePriorityFields(
  value: ExecutivePriorityPresentation | null,
  t: (key: string) => string,
): StructuredField[] {
  if (!value) {
    return [];
  }
  return [
    { label: t("companyInputs.executivePriorityAttentionLevel"), value: value.attentionLevel },
    { label: t("companyInputs.executivePrioritySituation"), value: value.situation },
    { label: t("companyInputs.executivePriorityBusinessRisk"), value: value.businessRisk },
    { label: t("companyInputs.executivePriorityTrigger"), value: value.executiveTrigger },
  ];
}

function executiveAssessmentFields(
  value: ExecutiveAssessmentPresentation | null,
  t: (key: string) => string,
): StructuredField[] {
  if (!value) {
    return [];
  }
  return [
    { label: t("companyInputs.executiveAssessmentInterpretation"), value: value.executiveInterpretation },
    { label: t("companyInputs.executiveAssessmentBusinessMeaning"), value: value.businessMeaning },
    {
      label: t("companyInputs.executiveAssessmentRecommendationContext"),
      value: value.executiveRecommendationContext,
    },
  ];
}

function BusinessImpactSection({
  detail,
  legacyBody,
}: {
  detail: BusinessImpactPresentation | null;
  legacyBody: string;
}) {
  const { t } = useLanguage();
  if (!detail) {
    return <BriefSection title={t("companyInputs.businessImpact")} body={legacyBody} />;
  }
  return (
    <div className="rounded-md border border-emerald-100 bg-white p-3">
      <div className="text-xs font-semibold uppercase text-emerald-800">{t("companyInputs.businessImpact")}</div>
      <div className="mt-2 space-y-2 text-sm leading-6 text-emerald-950">
        <div>
          <span className="font-semibold">{t("companyInputs.businessImpactOperational")}: </span>
          {detail.operational}
        </div>
        <div>
          <span className="font-semibold">{t("companyInputs.businessImpactFinancial")}: </span>
          {detail.financial || t("companyInputs.businessImpactFinancialUnknown")}
        </div>
        <div>
          <span className="font-semibold">{t("companyInputs.businessImpactStrategic")}: </span>
          <PendingOrText value={detail.strategic} />
        </div>
      </div>
    </div>
  );
}

function ExecutiveActionsSection({
  actions,
  legacyItems,
}: {
  actions: ExecutiveActionPresentation[];
  legacyItems: string[];
}) {
  const { t } = useLanguage();
  if (actions.length === 0) {
    return <BriefSection title={t("companyInputs.recommendedExecutiveActions")} items={legacyItems} />;
  }
  return (
    <div className="rounded-md border border-emerald-100 bg-white p-3 lg:col-span-2">
      <div className="text-xs font-semibold uppercase text-emerald-800">{t("companyInputs.recommendedExecutiveActions")}</div>
      <ul className="mt-2 space-y-2">
        {actions.map((action, index) => (
          <li
            key={`${action.action}-${index}`}
            className="rounded border border-emerald-100 bg-emerald-50/40 p-2 text-sm text-emerald-950"
          >
            <div className="font-medium">{action.action}</div>
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-emerald-900">
              <span>
                {t("companyInputs.executiveActionPriority")}: <PriorityValue value={action.priority} />
              </span>
              <span>
                {t("companyInputs.executiveActionReason")}: <PendingOrText value={action.reason} />
              </span>
              <span>
                {t("companyInputs.executiveActionExpectedOutcome")}: <PendingOrText value={action.expectedOutcome} />
              </span>
              <span>
                {t("companyInputs.executiveActionOwner")}: {action.owner}
              </span>
            </div>
            {action.evidenceRefs.length > 0 ? (
              <div className="mt-1 text-xs text-emerald-800">
                {t("companyInputs.executiveActionEvidence")}: {action.evidenceRefs.join(", ")}
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ExecutiveAttentionSection({ attention }: { attention: ExecutiveAttentionPresentation | null }) {
  const { t } = useLanguage();
  if (!attention) {
    return null;
  }
  return (
    <div className="rounded-md border border-emerald-100 bg-white p-3">
      <div className="text-xs font-semibold uppercase text-emerald-800">{t("companyInputs.executiveAttention")}</div>
      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        <div>
          <div className="text-xs font-semibold text-emerald-700">{t("companyInputs.executiveAttentionImmediate")}</div>
          {attention.immediate.length > 0 ? (
            <ul className="mt-1 space-y-1 text-sm text-emerald-950">
              {attention.immediate.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-sm text-emerald-900">—</p>
          )}
        </div>
        <div>
          <div className="text-xs font-semibold text-emerald-700">{t("companyInputs.executiveAttentionMonitor")}</div>
          {attention.monitor.length > 0 ? (
            <ul className="mt-1 space-y-1 text-sm text-emerald-950">
              {attention.monitor.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-sm text-emerald-900">—</p>
          )}
        </div>
      </div>
    </div>
  );
}

function BriefSection({
  title,
  body,
  items,
  empty,
}: {
  title: string;
  body?: string;
  items?: string[];
  empty?: string;
}) {
  const cleanedItems = items?.filter(Boolean) ?? [];

  return (
    <div className="rounded-md border border-emerald-100 bg-white p-3">
      <div className="text-xs font-semibold uppercase text-emerald-800">{title}</div>
      {body ? <p className="mt-1 text-sm leading-6 text-emerald-950">{body}</p> : null}
      {cleanedItems.length > 0 ? (
        <ul className="mt-2 space-y-1 text-sm leading-6 text-emerald-950">
          {cleanedItems.map((item, index) => (
            <li key={`${title}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : null}
      {!body && cleanedItems.length === 0 ? (
        <p className="mt-1 text-sm leading-6 text-emerald-900">{empty}</p>
      ) : null}
    </div>
  );
}

function ResultField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs font-semibold uppercase text-muted">{label}</div>
      <div className="mt-1 truncate text-sm font-medium text-ink" title={value}>
        {value}
      </div>
    </div>
  );
}

function resultFromFile(
  uploaded: CompanyFile,
  department: Department | null,
  language: "en" | "ar",
  t: (key: string) => string,
): RuntimeResult {
  const runtime = asRecord(uploaded.metadata.nco_lite);
  const classification = asRecord(runtime.classification);
  const evidencePolicy = asRecord(runtime.evidence_policy);
  const runtimeStatus = mapRuntimeStatus(String(runtime.nco_status || uploaded.status || "completed"));
  const pipeline = businessPipelineLabel(String(classification.probable_pipeline || ""), uploaded.filename, t);
  const confidencePercentage = confidencePercentageLabel(classification.confidence);
  const evidence = missingEvidence(runtime, t);
  const companyInputs = recommendedCompanyInputs(evidence, t);

  return {
    sourceLabel: uploaded.filename,
    classification: businessCategoryLabel(String(classification.input_category || ""), uploaded.filename, t),
    department: departmentLabel(String(classification.probable_department || ""), department, language, t),
    pipeline,
    confidence: evidencePolicy.confidence
      ? policyConfidenceLabel(String(evidencePolicy.confidence), t)
      : confidenceLabel(classification.confidence, t),
    confidenceReason: String(evidencePolicy.confidence_reduction_reason || "").trim() || null,
    runtimeStatus,
    missingEvidence: evidence,
    ceoBrief: firstCEOBrief(runtime, confidencePercentage, evidence, companyInputs, t),
  };
}

function resultFromText(
  response: OperationalInputResponse,
  department: Department | null,
  language: "en" | "ar",
  t: (key: string) => string,
): RuntimeResult {
  const classification = asRecord(response.classification);
  return {
    sourceLabel: t("companyInputs.text"),
    classification: businessCategoryLabel(String(classification.category || response.category || "daily_update"), "", t),
    department: departmentLabel(String(classification.inferred_department || ""), department, language, t),
    pipeline: t("companyInputs.pipelineOperationalUpdate"),
    confidence: confidenceLabel(classification.confidence, t),
    confidenceReason: null,
    runtimeStatus: "completed",
    missingEvidence: [],
    ceoBrief: null,
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function businessCategoryLabel(category: string, filename: string, t: (key: string) => string): string {
  const normalized = category.toLowerCase();
  if (normalized === "operational" || normalized === "daily_update") {
    return t("companyInputs.categoryOperational");
  }
  if (normalized === "financial") {
    return t("companyInputs.categoryFinancial");
  }
  if (normalized === "knowledge") {
    return t("companyInputs.categoryKnowledge");
  }
  if (filename.toLowerCase().endsWith(".pdf")) {
    return t("companyInputs.categoryKnowledge");
  }
  return t("companyInputs.categoryReview");
}

function businessPipelineLabel(pipeline: string, filename: string, t: (key: string) => string): string {
  if (pipeline === "excel_poultry_report") {
    return t("companyInputs.pipelinePoultryReport");
  }
  if (filename.toLowerCase().endsWith(".pdf")) {
    return t("companyInputs.pipelineDocumentReview");
  }
  if (filename) {
    return t("companyInputs.pipelineFileReview");
  }
  return t("companyInputs.pipelineReview");
}

function departmentLabel(
  detected: string,
  selected: Department | null,
  language: "en" | "ar",
  t: (key: string) => string,
): string {
  if (detected === "dairtna_poultry") {
    return t("companyInputs.departmentDairtna");
  }
  if (detected) {
    return detected.replace(/_/g, " ");
  }
  if (selected) {
    return localizeDepartmentName(selected.name, language);
  }
  return t("companyWideScope");
}

function confidenceLabel(value: unknown, t: (key: string) => string): string {
  if (typeof value === "number") {
    return `${Math.round(value * 100)}%`;
  }
  return t("companyInputs.confidencePending");
}

function confidencePercentageLabel(value: unknown): string | null {
  if (typeof value !== "number") {
    return null;
  }
  return `${Math.round(value * 100)}%`;
}

function policyConfidenceLabel(value: string, t: (key: string) => string): string {
  if (value === "reduced") {
    return t("companyInputs.confidenceReduced");
  }
  if (value === "high") {
    return t("companyInputs.confidenceHigh");
  }
  return value;
}

function mapRuntimeStatus(status: string): RuntimeState {
  if (status === "waiting_for_input_confirmation") {
    return "waiting_confirmation";
  }
  if (status === "waiting_for_missing_evidence") {
    return "waiting_evidence";
  }
  if (status === "failed" || status === "error") {
    return "failed";
  }
  if (status === "completed" || status === "ready" || status === "processed") {
    return "completed";
  }
  return "completed";
}

function statusLabel(status: RuntimeState, t: (key: string) => string): string {
  const labels: Record<RuntimeState, string> = {
    idle: "",
    processing: t("companyInputs.processing"),
    waiting_confirmation: t("companyInputs.waitingConfirmation"),
    waiting_evidence: t("companyInputs.waitingEvidence"),
    completed: t("companyInputs.completed"),
    failed: t("companyInputs.failedSafely"),
  };
  return labels[status];
}

function missingEvidence(runtime: Record<string, unknown>, t: (key: string) => string): string[] {
  const evidence = runtime.missing_evidence;
  if (!Array.isArray(evidence)) {
    const count = runtime.missing_evidence_count;
    return typeof count === "number" && count > 0 ? [t("companyInputs.missingEvidenceGeneric")] : [];
  }
  return evidence.map((item) => evidenceLabel(item, t)).filter(Boolean).slice(0, 5);
}

function evidenceLabel(value: unknown, t: (key: string) => string): string {
  const record = asRecord(value);
  return String(record.description || record.reason || record.evidence_type || t("companyInputs.missingEvidenceGeneric"));
}

function firstCEOBrief(
  runtime: Record<string, unknown>,
  confidencePercentage: string | null,
  evidence: string[],
  companyInputs: string[],
  t: (key: string) => string,
): CEOBriefPresentation | null {
  const briefs = runtime.briefs;
  if (!Array.isArray(briefs)) {
    return null;
  }
  const first = asRecord(briefs[0]);
  const headline = String(first.headline || "").trim();
  const executiveSummary = String(first.summary || headline).trim();
  if (!executiveSummary) {
    return null;
  }

  const backendCompanyInputs = stringArray(first.recommended_company_inputs);

  return {
    briefId: String(first.brief_id || "CEO-BRIEF-1"),
    headline: headline || t("companyInputs.ceoBrief"),
    executivePriority: executivePriorityDetail(first.executive_priority),
    executiveSummary,
    whatChanged: statementList(first.what_changed),
    facts: statementList(first.facts),
    executiveAssessment: executiveAssessmentDetail(first.executive_assessment),
    businessImpact: String(first.business_impact || t("companyInputs.notAvailableFromRuntime")),
    businessImpactDetail: businessImpactDetail(first.business_impact_detail),
    executiveActions: executiveActionsList(first.executive_actions),
    recommendedActions: stringArray(first.recommended_actions),
    confidenceLevel: policyConfidenceLabel(String(first.confidence || ""), t),
    confidencePercentage,
    confidenceExplanation: String(first.confidence_explanation || "").trim(),
    missingEvidence: evidence,
    recommendedCompanyInputs: backendCompanyInputs.length > 0 ? backendCompanyInputs : companyInputs,
    executiveAttention: executiveAttentionDetail(first.executive_attention),
  };
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => String(item || "").trim()).filter(Boolean).slice(0, 5)
    : [];
}

function statementList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => String(asRecord(item).statement || "").trim()).filter(Boolean)
    : [];
}

function executivePriorityDetail(value: unknown): ExecutivePriorityPresentation | null {
  const record = asRecord(value);
  if (
    record.attention_level === undefined &&
    record.situation === undefined &&
    record.business_risk === undefined &&
    record.executive_trigger === undefined
  ) {
    return null;
  }
  return {
    attentionLevel: record.attention_level,
    situation: record.situation,
    businessRisk: record.business_risk,
    executiveTrigger: record.executive_trigger,
  };
}

function executiveAssessmentDetail(value: unknown): ExecutiveAssessmentPresentation | null {
  const record = asRecord(value);
  if (
    record.executive_interpretation === undefined &&
    record.business_meaning === undefined &&
    record.executive_recommendation_context === undefined
  ) {
    return null;
  }
  return {
    executiveInterpretation: record.executive_interpretation,
    businessMeaning: record.business_meaning,
    executiveRecommendationContext: record.executive_recommendation_context,
  };
}

function businessImpactDetail(value: unknown): BusinessImpactPresentation | null {
  const record = asRecord(value);
  if (!record.operational && !record.financial && !record.strategic) {
    return null;
  }
  return {
    operational: String(record.operational || ""),
    financial: String(record.financial || ""),
    strategic: record.strategic,
  };
}

function executiveActionsList(value: unknown): ExecutiveActionPresentation[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => {
      const record = asRecord(item);
      return {
        action: String(record.action || "").trim(),
        // Business Logic, not Executive Language — null (or any non-string)
        // means no priority-assignment rule has been approved yet.
        priority: typeof record.priority === "string" ? record.priority : null,
        reason: record.reason,
        expectedOutcome: record.expected_outcome,
        owner: String(record.owner || "").trim(),
        evidenceRefs: Array.isArray(record.evidence_refs) ? record.evidence_refs.map((ref) => String(ref)) : [],
      };
    })
    .filter((action) => action.action);
}

function executiveAttentionDetail(value: unknown): ExecutiveAttentionPresentation | null {
  const record = asRecord(value);
  const immediate = Array.isArray(record.immediate) ? record.immediate.map((item) => String(item)) : [];
  const monitor = Array.isArray(record.monitor) ? record.monitor.map((item) => String(item)) : [];
  if (immediate.length === 0 && monitor.length === 0) {
    return null;
  }
  return { immediate, monitor };
}

function recommendedCompanyInputs(evidence: string[], t: (key: string) => string): string[] {
  return evidence.length > 0
    ? evidence.map((item) => `${t("companyInputs.provideInputPrefix")} ${item}`)
    : [];
}

function localizeDepartmentName(value: string, language: "en" | "ar"): string {
  if (language === "en") {
    return value;
  }

  const names: Record<string, string> = {
    CEO: "الإدارة التنفيذية",
    Sales: "المبيعات",
    Finance: "المالية",
    Marketing: "التسويق",
    Operations: "العمليات",
  };
  return names[value] || value;
}
