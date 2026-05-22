"use client";

import { FormEvent, useMemo, useState } from "react";

import { useLanguage } from "@/components/i18n/LanguageProvider";
import { ApiError } from "@/lib/api/client";
import { uploadFile } from "@/lib/api/files";
import { submitOperationalInput } from "@/lib/api/operational-inputs";
import type { Department, OperationalInputResponse } from "@/lib/types";

type OperationalInputPanelProps = {
  token: string;
  department: Department | null;
  departments: Department[];
  canSubmit: boolean;
  canUpload: boolean;
  canAssignDepartment: boolean;
};

type AttachedFile = {
  id: string;
  filename: string;
};

const categories = ["daily_update", "kpi", "issue", "decision", "report", "document", "alert", "note"] as const;
const priorities = ["low", "normal", "watch", "high", "critical"] as const;

export function OperationalInputPanel({
  token,
  department,
  departments,
  canSubmit,
  canUpload,
  canAssignDepartment,
}: OperationalInputPanelProps) {
  const { t } = useLanguage();
  const [text, setText] = useState("");
  const [category, setCategory] = useState<(typeof categories)[number]>("daily_update");
  const [priority, setPriority] = useState<(typeof priorities)[number]>("normal");
  const [eventDate, setEventDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [metricName, setMetricName] = useState("");
  const [metricValue, setMetricValue] = useState("");
  const [targetDepartmentId, setTargetDepartmentId] = useState<string>("");
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [activity, setActivity] = useState<OperationalInputResponse[]>([]);
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "uploading" | "error">("idle");
  const [errorDetail, setErrorDetail] = useState("");

  const labels = useMemo(
    () => ({
      title: t("operations.input.title"),
      subtitle: t("operations.input.subtitle"),
      category: t("operations.input.category"),
      priority: t("operations.input.priority"),
      date: t("operations.input.date"),
      target: t("operations.input.target"),
      note: t("operations.input.note"),
      notePlaceholder: t("operations.input.notePlaceholder"),
      metricName: t("operations.input.metricName"),
      metricValue: t("operations.input.metricValue"),
      upload: t("operations.input.upload"),
      uploading: t("operations.input.uploading"),
      save: t("operations.input.save"),
      saving: t("operations.input.saving"),
      recent: t("operations.input.recent"),
      companyWide: t("operations.input.companyWide"),
      executive: t("operations.input.executive"),
      restricted: t("operations.input.restricted"),
      saved: t("operations.input.saved"),
      error: t("operations.input.error"),
      hint: t("operations.input.hint"),
      noRecent: t("operations.input.noRecent"),
    }),
    [t],
  );

  const sourceDepartment = department;
  const selectedTarget = departments.find((item) => item.id === targetDepartmentId) ?? null;
  const scopedDepartmentId = canAssignDepartment ? targetDepartmentId || null : sourceDepartment?.id ?? null;
  const disabled = !canSubmit || status === "saving" || status === "uploading";

  async function handleUpload(file: File | null) {
    if (!file || !token || !canUpload) {
      return;
    }

    setStatus("uploading");
    setErrorDetail("");
    try {
      const uploaded = await uploadFile(token, file, scopedDepartmentId);
      setAttachedFiles((current) => [...current, { id: uploaded.id, filename: uploaded.filename }]);
      setStatus("idle");
    } catch (caught) {
      setErrorDetail(caught instanceof ApiError ? caught.detail : labels.error);
      setStatus("error");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (disabled) {
      return;
    }

    const metrics = metricName.trim() && metricValue.trim() ? { [metricName.trim()]: metricValue.trim() } : {};
    setStatus("saving");
    setErrorDetail("");
    try {
      const response = await submitOperationalInput(token, {
        department_id: sourceDepartment?.id ?? null,
        department_type: sourceDepartment?.department_type ?? null,
        target_department_id: canAssignDepartment ? targetDepartmentId || null : null,
        target_department_type: canAssignDepartment ? selectedTarget?.department_type ?? null : null,
        category,
        priority,
        event_date: eventDate || null,
        text,
        metrics,
        files_attached: attachedFiles,
        payload: {
          workspace: sourceDepartment?.slug ?? "ceo",
        },
      });
      setActivity((current) => [response, ...current].slice(0, 5));
      setText("");
      setMetricName("");
      setMetricValue("");
      setAttachedFiles([]);
      setStatus("saved");
    } catch (caught) {
      setErrorDetail(caught instanceof ApiError ? caught.detail : labels.error);
      setStatus("error");
    }
  }

  return (
    <section className="panel p-4">
      <div className="flex flex-col justify-between gap-3 border-b border-line pb-3 sm:flex-row sm:items-start">
        <div>
          <div className="executive-label">{department ? department.name : labels.executive}</div>
          <h2 className="mt-1 text-base font-semibold text-ink">{labels.title}</h2>
          <p className="mt-1 text-sm leading-6 text-muted">{labels.subtitle}</p>
        </div>
        <span className="rounded-md border border-line bg-surface px-2.5 py-1.5 text-xs text-muted">
          {department ? department.name : labels.companyWide}
        </span>
      </div>

      <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
        <div className="grid gap-3 md:grid-cols-4">
          <label className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">{labels.category}</span>
            <select className="input" disabled={disabled} value={category} onChange={(event) => setCategory(event.target.value as typeof category)}>
              {categories.map((item) => (
                <option key={item} value={item}>
                  {t(`operations.input.categories.${item}`)}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">{labels.priority}</span>
            <select className="input" disabled={disabled} value={priority} onChange={(event) => setPriority(event.target.value as typeof priority)}>
              {priorities.map((item) => (
                <option key={item} value={item}>
                  {t(`operations.input.priorities.${item}`)}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">{labels.date}</span>
            <input className="input" disabled={disabled} type="date" value={eventDate} onChange={(event) => setEventDate(event.target.value)} />
          </label>
          <label className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">{labels.target}</span>
            <select
              className="input"
              disabled={disabled || !canAssignDepartment}
              value={canAssignDepartment ? targetDepartmentId : sourceDepartment?.id ?? ""}
              onChange={(event) => setTargetDepartmentId(event.target.value)}
            >
              <option value="">{labels.companyWide}</option>
              {departments.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="block space-y-1.5">
          <span className="text-xs font-semibold uppercase text-muted">{labels.note}</span>
          <textarea
            className="input min-h-24 resize-none leading-6"
            disabled={disabled}
            placeholder={labels.notePlaceholder}
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        </label>

        <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
          <label className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">{labels.metricName}</span>
            <input className="input" disabled={disabled} value={metricName} onChange={(event) => setMetricName(event.target.value)} />
          </label>
          <label className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">{labels.metricValue}</span>
            <input className="input" disabled={disabled} value={metricValue} onChange={(event) => setMetricValue(event.target.value)} />
          </label>
          <label className="button-secondary cursor-pointer px-3 py-2 text-center text-sm">
            {status === "uploading" ? labels.uploading : labels.upload}
            <input className="sr-only" disabled={disabled || !canUpload} type="file" onChange={(event) => handleUpload(event.target.files?.[0] ?? null)} />
          </label>
        </div>

        {attachedFiles.length > 0 ? (
          <div className="flex flex-wrap gap-2 text-xs text-muted">
            {attachedFiles.map((file) => (
              <span key={file.id || file.filename} className="rounded border border-line bg-surface px-2 py-1">
                {file.filename}
              </span>
            ))}
          </div>
        ) : null}

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-muted">
            {!canSubmit
              ? labels.restricted
              : status === "saved"
                ? labels.saved
                : status === "error"
                  ? errorDetail || labels.error
                  : labels.hint}
          </div>
          <button className="button-primary sm:w-36" type="submit" disabled={disabled || (!text.trim() && attachedFiles.length === 0 && !metricValue.trim())}>
            {status === "saving" ? labels.saving : labels.save}
          </button>
        </div>
      </form>

      <div className="mt-4 border-t border-line pt-3">
        <div className="text-xs font-semibold uppercase text-muted">{labels.recent}</div>
        <div className="mt-2 space-y-2">
          {activity.length === 0 ? (
            <div className="rounded-md border border-line bg-surface px-3 py-2 text-sm text-muted">{labels.noRecent}</div>
          ) : (
            activity.map((item) => (
              <div key={`${item.event_type}-${item.summary}`} className="rounded-md border border-line bg-surface px-3 py-2">
                <div className="text-xs font-semibold uppercase text-muted">
                  {t(`operations.input.categories.${item.category}`)} | {t(`operations.input.priorities.${item.priority}`)}
                </div>
                <div className="mt-1 text-sm text-ink">{item.summary}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
