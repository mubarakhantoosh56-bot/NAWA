"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { useLanguage } from "@/components/i18n/LanguageProvider";
import { createOperationalEvent, listOperationalEvents } from "@/lib/api/operational-events";
import type {
  Department,
  OperationalEvent,
  OperationalEventCreateRequest,
  OperationalEventPriority,
} from "@/lib/types";

type ManualOperationalEventPanelProps = {
  token: string;
  departments: Department[];
  defaultDepartment: Department | null;
  canSubmit: boolean;
};

type TemplateKey = "mortality_report" | "feed_issue" | "veterinary_issue";

type TemplateConfig = {
  labelKey: string;
  eventType: string;
  category: string;
  defaultPriority: OperationalEventPriority;
  titleKey: string;
  summaryPlaceholderKey: string;
  fields: Array<{
    key: string;
    labelKey: string;
    placeholderKey: string;
    required?: boolean;
  }>;
};

const templates: Record<TemplateKey, TemplateConfig> = {
  mortality_report: {
    labelKey: "operations.manual.templates.mortality_report.label",
    eventType: "operational.dairtna.mortality",
    category: "mortality",
    defaultPriority: "critical",
    titleKey: "operations.manual.templates.mortality_report.title",
    summaryPlaceholderKey: "operations.manual.templates.mortality_report.placeholder",
    fields: [
      { key: "hall", labelKey: "operations.manual.templates.mortality_report.hall", placeholderKey: "operations.manual.templates.mortality_report.hallPlaceholder", required: true },
      { key: "mortality_count", labelKey: "operations.manual.templates.mortality_report.mortalityCount", placeholderKey: "operations.manual.templates.mortality_report.mortalityCountPlaceholder", required: true },
      { key: "flock_age", labelKey: "operations.manual.templates.mortality_report.flockAge", placeholderKey: "operations.manual.templates.mortality_report.flockAgePlaceholder" },
      { key: "observed_symptoms", labelKey: "operations.manual.templates.mortality_report.observedSymptoms", placeholderKey: "operations.manual.templates.mortality_report.observedSymptomsPlaceholder" },
    ],
  },
  feed_issue: {
    labelKey: "operations.manual.templates.feed_issue.label",
    eventType: "operational.dairtna.feed_shortage",
    category: "feed_shortage",
    defaultPriority: "high",
    titleKey: "operations.manual.templates.feed_issue.title",
    summaryPlaceholderKey: "operations.manual.templates.feed_issue.placeholder",
    fields: [
      { key: "hall_or_area", labelKey: "operations.manual.templates.feed_issue.hallOrArea", placeholderKey: "operations.manual.templates.feed_issue.hallOrAreaPlaceholder", required: true },
      { key: "feed_type", labelKey: "operations.manual.templates.feed_issue.feedType", placeholderKey: "operations.manual.templates.feed_issue.feedTypePlaceholder" },
      { key: "available_quantity", labelKey: "operations.manual.templates.feed_issue.availableQuantity", placeholderKey: "operations.manual.templates.feed_issue.availableQuantityPlaceholder" },
      { key: "expected_impact", labelKey: "operations.manual.templates.feed_issue.expectedImpact", placeholderKey: "operations.manual.templates.feed_issue.expectedImpactPlaceholder" },
    ],
  },
  veterinary_issue: {
    labelKey: "operations.manual.templates.veterinary_issue.label",
    eventType: "operational.dairtna.medicine_delay",
    category: "medicine_delay",
    defaultPriority: "high",
    titleKey: "operations.manual.templates.veterinary_issue.title",
    summaryPlaceholderKey: "operations.manual.templates.veterinary_issue.placeholder",
    fields: [
      { key: "hall", labelKey: "operations.manual.templates.veterinary_issue.hall", placeholderKey: "operations.manual.templates.veterinary_issue.hallPlaceholder", required: true },
      { key: "medicine_or_issue", labelKey: "operations.manual.templates.veterinary_issue.medicineOrIssue", placeholderKey: "operations.manual.templates.veterinary_issue.medicineOrIssuePlaceholder", required: true },
      { key: "requested_date", labelKey: "operations.manual.templates.veterinary_issue.requestedDate", placeholderKey: "operations.manual.templates.veterinary_issue.requestedDatePlaceholder" },
      { key: "veterinary_owner", labelKey: "operations.manual.templates.veterinary_issue.veterinaryOwner", placeholderKey: "operations.manual.templates.veterinary_issue.veterinaryOwnerPlaceholder" },
    ],
  },
};

const priorities: OperationalEventPriority[] = ["watch", "high", "critical"];

export function ManualOperationalEventPanel({
  token,
  departments,
  defaultDepartment,
  canSubmit,
}: ManualOperationalEventPanelProps) {
  const { t } = useLanguage();
  const [templateKey, setTemplateKey] = useState<TemplateKey>("mortality_report");
  const [departmentId, setDepartmentId] = useState(defaultDepartment?.id ?? "");
  const [priority, setPriority] = useState<OperationalEventPriority>(templates.mortality_report.defaultPriority);
  const [eventDateTime, setEventDateTime] = useState(() => toLocalDateTimeValue(new Date()));
  const [summary, setSummary] = useState("");
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [recentEvents, setRecentEvents] = useState<OperationalEvent[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "saving" | "saved" | "error">("idle");
  const [isOpen, setIsOpen] = useState(false);

  const template = templates[templateKey];
  const disabled = !canSubmit || status === "saving";
  const selectedDepartment = departments.find((department) => department.id === departmentId) ?? defaultDepartment;

  useEffect(() => {
    if (!departmentId && defaultDepartment?.id) {
      setDepartmentId(defaultDepartment.id);
    }
  }, [defaultDepartment, departmentId]);

  useEffect(() => {
    setPriority(templates[templateKey].defaultPriority);
    setFieldValues({});
    setSummary("");
  }, [templateKey]);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isMounted = true;
    setStatus((current) => (current === "idle" ? "loading" : current));
    listOperationalEvents(token, 5)
      .then((response) => {
        if (!isMounted) {
          return;
        }
        setRecentEvents(
          response.events.filter((event) => event.metadata?.division === "Dairtna Poultry").slice(0, 3),
        );
        setStatus((current) => (current === "loading" ? "idle" : current));
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setStatus((current) => (current === "loading" ? "idle" : current));
      });

    return () => {
      isMounted = false;
    };
  }, [token]);

  const requiredMissing = useMemo(
    () =>
      template.fields.some(
        (field) => field.required && !String(fieldValues[field.key] || "").trim(),
      ) || !summary.trim(),
    [fieldValues, summary, template.fields],
  );

  function updateField(key: string, value: string) {
    setFieldValues((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (disabled || requiredMissing) {
      return;
    }

    const timestamp = eventDateTime ? new Date(eventDateTime).toISOString() : new Date().toISOString();
    const payload: OperationalEventCreateRequest = {
      department_id: selectedDepartment?.id ?? null,
      event_type: template.eventType,
      category: template.category,
      priority,
      title: t(template.titleKey),
      summary: summary.trim(),
      event_timestamp: timestamp,
      source_type: "manual_form",
      source_ref: null,
      payload: {
        division: "Dairtna Poultry",
        department_name: selectedDepartment?.name ?? null,
        template: templateKey,
        fields: cleanFields(fieldValues),
      },
      metadata: {
        division: "Dairtna Poultry",
        entry_mode: "manual_field_form",
        template: templateKey,
      },
    };

    setStatus("saving");
    try {
      const created = await createOperationalEvent(token, payload);
      setRecentEvents((current) => [created, ...current].slice(0, 3));
      setSummary("");
      setFieldValues({});
      setEventDateTime(toLocalDateTimeValue(new Date()));
      setStatus("saved");
    } catch {
      setStatus("error");
    }
  }

  return (
    <section className="panel p-4">
      <button
        className="flex w-full flex-col justify-between gap-3 text-left sm:flex-row sm:items-start"
        type="button"
        onClick={() => setIsOpen((current) => !current)}
      >
        <div>
          <div className="executive-label">{t("operations.manual.label")}</div>
          <h2 className="mt-1 text-base font-semibold text-ink">{t("operations.manual.title")}</h2>
          <p className="mt-1 text-sm leading-6 text-muted">
            {t("operations.manual.description")}
          </p>
        </div>
        <span className="rounded-md border border-line bg-surface px-2.5 py-1.5 text-xs text-muted">
          {isOpen ? t("operations.manual.hide") : t("operations.manual.show")}
        </span>
      </button>

      {isOpen ? (
      <form className="mt-4 space-y-4 border-t border-line pt-4" onSubmit={handleSubmit}>
        <div className="grid gap-3 md:grid-cols-4">
          <label className="space-y-1.5 md:col-span-2">
            <span className="text-xs font-semibold uppercase text-muted">{t("operations.manual.reportType")}</span>
            <select
              className="input"
              disabled={disabled}
              value={templateKey}
              onChange={(event) => setTemplateKey(event.target.value as TemplateKey)}
            >
              {Object.entries(templates).map(([key, item]) => (
                <option key={key} value={key}>
                  {t(item.labelKey)}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">{t("operations.manual.priority")}</span>
            <select
              className="input"
              disabled={disabled}
              value={priority}
              onChange={(event) => setPriority(event.target.value as OperationalEventPriority)}
            >
              {priorities.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">{t("operations.manual.eventTime")}</span>
            <input
              className="input"
              disabled={disabled}
              type="datetime-local"
              value={eventDateTime}
              onChange={(event) => setEventDateTime(event.target.value)}
            />
          </label>
        </div>

        <label className="space-y-1.5">
          <span className="text-xs font-semibold uppercase text-muted">{t("operations.manual.department")}</span>
          <select
            className="input"
            disabled={disabled || departments.length === 0}
            value={departmentId}
            onChange={(event) => setDepartmentId(event.target.value)}
          >
            <option value="">{t("operations.manual.companyWideTimeline")}</option>
            {departments.map((department) => (
              <option key={department.id} value={department.id}>
                {department.name}
              </option>
            ))}
          </select>
        </label>

        <div className="grid gap-3 md:grid-cols-2">
          {template.fields.map((field) => (
            <label key={field.key} className="space-y-1.5">
              <span className="text-xs font-semibold uppercase text-muted">
                {t(field.labelKey)}
                {field.required ? " *" : ""}
              </span>
              <input
                className="input"
                disabled={disabled}
                placeholder={t(field.placeholderKey)}
                value={fieldValues[field.key] || ""}
                onChange={(event) => updateField(field.key, event.target.value)}
              />
            </label>
          ))}
        </div>

        <label className="block space-y-1.5">
          <span className="text-xs font-semibold uppercase text-muted">{t("operations.manual.fieldSummary")}</span>
          <textarea
            className="input min-h-24 resize-none leading-6"
            disabled={disabled}
            placeholder={t(template.summaryPlaceholderKey)}
            value={summary}
            onChange={(event) => setSummary(event.target.value)}
          />
        </label>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-muted">
            {!canSubmit
              ? t("operations.manual.restricted")
              : status === "saved"
                ? t("operations.manual.saved")
                : status === "error"
                  ? t("operations.manual.error")
                  : t("operations.manual.hint")}
          </div>
          <button className="button-primary sm:w-40" type="submit" disabled={disabled || requiredMissing}>
            {status === "saving" ? t("operations.manual.saving") : t("operations.manual.submit")}
          </button>
        </div>
      </form>
      ) : null}

      {isOpen ? (
      <div className="mt-4 border-t border-line pt-3">
        <div className="text-xs font-semibold uppercase text-muted">{t("operations.manual.recentEntries")}</div>
        <div className="mt-2 space-y-2">
          {recentEvents.length === 0 ? (
            <div className="rounded-md border border-line bg-surface px-3 py-2 text-sm text-muted">
              {t("operations.manual.noRecent")}
            </div>
          ) : (
            recentEvents.map((event) => (
              <div key={event.id} className="rounded-md border border-line bg-surface px-3 py-2">
                <div className="text-xs font-semibold uppercase text-muted">
                  {event.category} | {event.priority}
                </div>
                <div className="mt-1 text-sm font-medium text-ink">{event.title}</div>
                <div className="mt-1 text-sm text-muted">{event.summary}</div>
              </div>
            ))
          )}
        </div>
      </div>
      ) : null}
    </section>
  );
}

function cleanFields(values: Record<string, string>): Record<string, string> {
  return Object.fromEntries(
    Object.entries(values)
      .map(([key, value]) => [key, value.split(/\s+/).join(" ").trim()])
      .filter(([, value]) => value),
  );
}

function toLocalDateTimeValue(date: Date): string {
  const offsetMs = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}
