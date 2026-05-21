"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

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
  label: string;
  eventType: string;
  category: string;
  defaultPriority: OperationalEventPriority;
  title: string;
  summaryPlaceholder: string;
  fields: Array<{
    key: string;
    label: string;
    placeholder: string;
    required?: boolean;
  }>;
};

const templates: Record<TemplateKey, TemplateConfig> = {
  mortality_report: {
    label: "Mortality Report",
    eventType: "operational.dairtna.mortality",
    category: "mortality",
    defaultPriority: "critical",
    title: "Mortality Report",
    summaryPlaceholder: "Example: Hall 4 reported increased mortality during the morning check.",
    fields: [
      { key: "hall", label: "Hall", placeholder: "Hall 4", required: true },
      { key: "mortality_count", label: "Mortality count", placeholder: "42", required: true },
      { key: "flock_age", label: "Flock age", placeholder: "31 days" },
      { key: "observed_symptoms", label: "Observed symptoms", placeholder: "Low movement, respiratory signs" },
    ],
  },
  feed_issue: {
    label: "Feed Shortage / Consumption Issue",
    eventType: "operational.dairtna.feed_shortage",
    category: "feed_shortage",
    defaultPriority: "high",
    title: "Feed Shortage",
    summaryPlaceholder: "Example: Feed delivery delay may affect Hall 2 and Hall 3 evening ration.",
    fields: [
      { key: "hall_or_area", label: "Hall or area", placeholder: "Hall 2 / silo area", required: true },
      { key: "feed_type", label: "Feed type", placeholder: "Starter / grower / layer" },
      { key: "available_quantity", label: "Available quantity", placeholder: "1.5 tons" },
      { key: "expected_impact", label: "Expected impact", placeholder: "Evening ration at risk" },
    ],
  },
  veterinary_issue: {
    label: "Medicine Delay / Veterinary Issue",
    eventType: "operational.dairtna.medicine_delay",
    category: "medicine_delay",
    defaultPriority: "high",
    title: "Medicine Delay",
    summaryPlaceholder: "Example: Requested medication has not arrived; veterinary follow-up is pending.",
    fields: [
      { key: "hall", label: "Hall", placeholder: "Hall 5", required: true },
      { key: "medicine_or_issue", label: "Medicine or issue", placeholder: "Antibiotic / vaccine / symptoms", required: true },
      { key: "requested_date", label: "Requested date", placeholder: "2026-05-21" },
      { key: "veterinary_owner", label: "Veterinary owner", placeholder: "Dr. name or team" },
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
      title: template.title,
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
          <div className="executive-label">Dairtna Poultry</div>
          <h2 className="mt-1 text-base font-semibold text-ink">Advanced structured entry</h2>
          <p className="mt-1 text-sm leading-6 text-muted">
            Use this when you already know the report type and structured details. No AI, automation, or situation grouping runs from this form.
          </p>
        </div>
        <span className="rounded-md border border-line bg-surface px-2.5 py-1.5 text-xs text-muted">
          {isOpen ? "Hide" : "Open"}
        </span>
      </button>

      {isOpen ? (
      <form className="mt-4 space-y-4 border-t border-line pt-4" onSubmit={handleSubmit}>
        <div className="grid gap-3 md:grid-cols-4">
          <label className="space-y-1.5 md:col-span-2">
            <span className="text-xs font-semibold uppercase text-muted">Report type</span>
            <select
              className="input"
              disabled={disabled}
              value={templateKey}
              onChange={(event) => setTemplateKey(event.target.value as TemplateKey)}
            >
              {Object.entries(templates).map(([key, item]) => (
                <option key={key} value={key}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">Priority</span>
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
            <span className="text-xs font-semibold uppercase text-muted">Event time</span>
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
          <span className="text-xs font-semibold uppercase text-muted">Department</span>
          <select
            className="input"
            disabled={disabled || departments.length === 0}
            value={departmentId}
            onChange={(event) => setDepartmentId(event.target.value)}
          >
            <option value="">Company-wide Dairtna timeline</option>
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
                {field.label}
                {field.required ? " *" : ""}
              </span>
              <input
                className="input"
                disabled={disabled}
                placeholder={field.placeholder}
                value={fieldValues[field.key] || ""}
                onChange={(event) => updateField(field.key, event.target.value)}
              />
            </label>
          ))}
        </div>

        <label className="block space-y-1.5">
          <span className="text-xs font-semibold uppercase text-muted">Field summary *</span>
          <textarea
            className="input min-h-24 resize-none leading-6"
            disabled={disabled}
            placeholder={template.summaryPlaceholder}
            value={summary}
            onChange={(event) => setSummary(event.target.value)}
          />
        </label>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-muted">
            {!canSubmit
              ? "Your current role cannot submit operational forms."
              : status === "saved"
                ? "Timeline event saved."
                : status === "error"
                  ? "Unable to save timeline event."
                  : "Required fields are intentionally minimal for field use."}
          </div>
          <button className="button-primary sm:w-40" type="submit" disabled={disabled || requiredMissing}>
            {status === "saving" ? "Saving..." : "Save to timeline"}
          </button>
        </div>
      </form>
      ) : null}

      {isOpen ? (
      <div className="mt-4 border-t border-line pt-3">
        <div className="text-xs font-semibold uppercase text-muted">Recent Dairtna timeline entries</div>
        <div className="mt-2 space-y-2">
          {recentEvents.length === 0 ? (
            <div className="rounded-md border border-line bg-surface px-3 py-2 text-sm text-muted">
              No timeline entries loaded in this session.
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
