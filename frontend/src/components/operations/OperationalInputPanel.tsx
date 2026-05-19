"use client";

import { FormEvent, useMemo, useState } from "react";

import { submitOperationalInput } from "@/lib/api/operational-inputs";
import { useLanguage } from "@/components/i18n/LanguageProvider";
import type { Department } from "@/lib/types";

type Field = {
  key: string;
  label: string;
  placeholder: string;
};

const FORM_FIELDS: Record<string, Field[]> = {
  production_ai: [
    { key: "production_quantity", label: "Production quantity", placeholder: "e.g. 18,400 cartons" },
    { key: "downtime", label: "Downtime", placeholder: "e.g. 45 minutes" },
    { key: "wastage", label: "Wastage", placeholder: "e.g. 2.1%" },
    { key: "line_issues", label: "Line issues", placeholder: "e.g. filler line stopped twice" },
  ],
  sales_ai: [
    { key: "daily_sales", label: "Daily sales", placeholder: "e.g. $42,000" },
    { key: "collections", label: "Collections", placeholder: "e.g. $18,500 collected" },
    { key: "market_issues", label: "Market issues", placeholder: "e.g. retailer stock-out complaints" },
  ],
  finance_ai: [
    { key: "expenses", label: "Expenses", placeholder: "e.g. fuel cost +8%" },
    { key: "payment_delays", label: "Payment delays", placeholder: "e.g. 3 key accounts delayed" },
    { key: "cashflow_notes", label: "Cashflow notes", placeholder: "e.g. collection gap next week" },
  ],
  marketing_ai: [
    { key: "campaign_status", label: "Campaign status", placeholder: "e.g. promo launch 70% ready" },
    { key: "launch_updates", label: "Launch updates", placeholder: "e.g. delayed by packaging approval" },
    { key: "competitor_notes", label: "Competitor notes", placeholder: "e.g. price cut in north region" },
  ],
};

type OperationalInputPanelProps = {
  token: string;
  department: Department | null;
  canSubmit: boolean;
};

export function OperationalInputPanel({ token, department, canSubmit }: OperationalInputPanelProps) {
  const { language } = useLanguage();
  const fields = useMemo(() => (department ? FORM_FIELDS[department.department_type] ?? [] : []), [department]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState("");
  const [severity, setSeverity] = useState<"normal" | "watch" | "high" | "critical">("normal");
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [summary, setSummary] = useState("");

  if (!department || fields.length === 0) {
    return null;
  }

  const title = language === "ar" ? "Ù…Ø¯Ø®Ù„Ø§Øª ØªØ´ØºÙŠÙ„ÙŠØ© ÙŠÙˆÙ…ÙŠØ©" : "Daily Operational Input";
  const subtitle =
    language === "ar"
      ? "ØªØ­ÙØ¸ Ù‡Ø°Ù‡ Ø§Ù„Ù…Ø¯Ø®Ù„Ø§Øª ÙƒØ£Ø­Ø¯Ø§Ø« Ø°Ø§ÙƒØ±Ø© Ù„ØªØ­Ø³ÙŠÙ† ØªÙˆØµÙŠØ§Øª NAWA."
      : "Submissions become operational memory for smarter NAWA recommendations.";
  const disabled = !canSubmit || status === "saving";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!department || disabled) {
      return;
    }

    setStatus("saving");
    setSummary("");
    try {
      const response = await submitOperationalInput(token, {
        department_id: department.id,
        department_type: department.department_type,
        form_type: "daily_input",
        metrics: values,
        notes,
        severity,
      });
      setStatus("saved");
      setSummary(response.summary);
      setValues({});
      setNotes("");
      setSeverity("normal");
    } catch {
      setStatus("error");
    }
  }

  return (
    <section className="panel p-4">
      <div className="flex flex-col justify-between gap-3 border-b border-line pb-3 sm:flex-row sm:items-start">
        <div>
          <div className="executive-label">{language === "ar" ? "Ø§Ù„ØªØ´ØºÙŠÙ„" : "Operations"}</div>
          <h2 className="mt-1 text-base font-semibold text-ink">{title}</h2>
          <p className="mt-1 text-sm leading-6 text-muted">{subtitle}</p>
        </div>
        <span className="rounded-md border border-line bg-surface px-2.5 py-1.5 text-xs text-muted">
          {department.name}
        </span>
      </div>

      <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
        <div className="grid gap-3 md:grid-cols-2">
          {fields.map((field) => (
            <label key={field.key} className="space-y-1.5">
              <span className="text-xs font-semibold uppercase text-muted">{field.label}</span>
              <input
                className="input"
                disabled={disabled}
                placeholder={field.placeholder}
                value={values[field.key] ?? ""}
                onChange={(event) => setValues((current) => ({ ...current, [field.key]: event.target.value }))}
              />
            </label>
          ))}
          <label className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">Severity</span>
            <select
              className="input"
              disabled={disabled}
              value={severity}
              onChange={(event) => setSeverity(event.target.value as "normal" | "watch" | "high" | "critical")}
            >
              <option value="normal">Normal</option>
              <option value="watch">Watch</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </label>
        </div>
        <label className="block space-y-1.5">
          <span className="text-xs font-semibold uppercase text-muted">Operational notes</span>
          <textarea
            className="input min-h-20 resize-none leading-6"
            disabled={disabled}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
        </label>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-muted">
            {!canSubmit
              ? "This form is restricted for your current role."
              : status === "saved"
                ? summary || "Operational event saved."
                : status === "error"
                  ? "Unable to save operational input."
                  : "Saved inputs feed memory and decision context."}
          </div>
          <button className="button-primary sm:w-36" type="submit" disabled={disabled}>
            {status === "saving" ? "Saving..." : "Save input"}
          </button>
        </div>
      </form>
    </section>
  );
}
