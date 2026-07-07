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
  briefSummary: string | null;
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

      {result.briefSummary ? (
        <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3">
          <div className="text-xs font-semibold uppercase text-emerald-800">{t("companyInputs.ceoBrief")}</div>
          <p className="mt-1 text-sm leading-6 text-emerald-900">{result.briefSummary}</p>
        </div>
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
  const briefSummary = firstBriefSummary(runtime);

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
    missingEvidence: missingEvidence(runtime, t),
    briefSummary,
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
    briefSummary: response.summary || null,
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

function firstBriefSummary(runtime: Record<string, unknown>): string | null {
  const briefs = runtime.briefs;
  if (!Array.isArray(briefs)) {
    return null;
  }
  const first = asRecord(briefs[0]);
  return String(first.summary || first.headline || "").trim() || null;
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
