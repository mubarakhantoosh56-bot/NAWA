"use client";

import { FormEvent, useEffect, useState } from "react";

import { createOperationalEvent } from "@/lib/api/operational-events";
import type {
  Department,
  OperationalEvent,
  OperationalEventCreateRequest,
  OperationalEventPriority,
} from "@/lib/types";

type NaturalOperationalCapturePanelProps = {
  token: string;
  departments: Department[];
  defaultDepartment: Department | null;
  canSubmit: boolean;
};

const priorities: OperationalEventPriority[] = ["normal", "watch", "high", "critical"];

export function NaturalOperationalCapturePanel({
  token,
  departments,
  defaultDepartment,
  canSubmit,
}: NaturalOperationalCapturePanelProps) {
  const [note, setNote] = useState("");
  const [priority, setPriority] = useState<OperationalEventPriority>("normal");
  const [departmentId, setDepartmentId] = useState(defaultDepartment?.id ?? "");
  const [recentEvents, setRecentEvents] = useState<OperationalEvent[]>([]);
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const scopedDepartment = resolveScopedDepartment(departments, defaultDepartment);
  const selectedDepartment = departments.find((department) => department.id === departmentId) ?? scopedDepartment;
  const hasSingleDepartmentScope = departments.length === 1 || Boolean(scopedDepartment);
  const disabled = !canSubmit || status === "saving";

  useEffect(() => {
    if (scopedDepartment?.id) {
      setDepartmentId(scopedDepartment.id);
    }
  }, [scopedDepartment]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedNote = note.trim();
    if (disabled || !cleanedNote) {
      return;
    }

    const payload: OperationalEventCreateRequest = {
      department_id: selectedDepartment?.id ?? null,
      event_type: "operational.manual_note",
      category: "daily_update",
      priority,
      title: buildTitle(cleanedNote),
      summary: cleanedNote,
      event_timestamp: new Date().toISOString(),
      source_type: "natural_capture",
      source_ref: null,
      payload: {
        raw_note: cleanedNote,
        department_name: selectedDepartment?.name ?? null,
      },
      metadata: {
        division: "Dairtna Poultry",
        entry_mode: "natural_operational_capture",
        needs_classification: true,
        template: "natural_capture",
      },
    };

    setStatus("saving");
    try {
      const created = await createOperationalEvent(token, payload);
      setRecentEvents((current) => [created, ...current].slice(0, 3));
      setNote("");
      setPriority("normal");
      setStatus("saved");
    } catch {
      setStatus("error");
    }
  }

  return (
    <section className="panel p-4">
      <div className="flex flex-col justify-between gap-3 border-b border-line pb-3 sm:flex-row sm:items-start">
        <div>
          <div className="executive-label">Dairtna Poultry</div>
          <h2 className="mt-1 text-lg font-semibold text-ink">What happened today?</h2>
          <p className="mt-1 text-sm leading-6 text-muted">
            Write the field update in plain language. NAWA stores it in the operational timeline for later review and classification.
          </p>
        </div>
        <span className="rounded-md border border-line bg-surface px-2.5 py-1.5 text-xs text-muted">
          natural_capture
        </span>
      </div>

      <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
        <label className="block space-y-1.5">
          <span className="text-xs font-semibold uppercase text-muted">Field note</span>
          <textarea
            className="input min-h-40 resize-none leading-6"
            disabled={disabled}
            placeholder="Example: Hall 4 had unusual mortality today. The team noticed lower movement and asked veterinary to check before evening."
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
        </label>

        <div className="grid gap-3 md:grid-cols-3">
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

          {hasSingleDepartmentScope ? (
            <div className="space-y-1.5 md:col-span-1">
              <span className="text-xs font-semibold uppercase text-muted">Department context</span>
              <div className="input bg-surface text-muted">{selectedDepartment?.name ?? "Dairtna Poultry"}</div>
            </div>
          ) : (
            <label className="space-y-1.5 md:col-span-1">
              <span className="text-xs font-semibold uppercase text-muted">Optional department context</span>
              <select
                className="input"
                disabled={disabled || departments.length === 0}
                value={departmentId}
                onChange={(event) => setDepartmentId(event.target.value)}
              >
                <option value="">No department selected</option>
                {departments.map((department) => (
                  <option key={department.id} value={department.id}>
                    {department.name}
                  </option>
                ))}
              </select>
            </label>
          )}

          <div className="space-y-1.5">
            <span className="text-xs font-semibold uppercase text-muted">Attachment</span>
            <div className="input bg-surface text-muted">Attachment placeholder</div>
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-muted">
            {!canSubmit
              ? "Your current role cannot submit operational forms."
              : status === "saved"
                ? "Sent to the operational timeline."
                : status === "error"
                  ? "Unable to send this note."
                  : "This does not run AI, correlation, or situation grouping."}
          </div>
          <button className="button-primary sm:w-36" type="submit" disabled={disabled || !note.trim()}>
            {status === "saving" ? "Sending..." : "Send to NAWA"}
          </button>
        </div>
      </form>

      {recentEvents.length > 0 ? (
        <div className="mt-4 border-t border-line pt-3">
          <div className="text-xs font-semibold uppercase text-muted">Sent this session</div>
          <div className="mt-2 space-y-2">
            {recentEvents.map((event) => (
              <div key={event.id} className="rounded-md border border-line bg-surface px-3 py-2">
                <div className="text-xs font-semibold uppercase text-muted">
                  {event.category} | {event.priority}
                </div>
                <div className="mt-1 text-sm text-ink">{event.summary}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function resolveScopedDepartment(
  departments: Department[],
  defaultDepartment: Department | null,
): Department | null {
  if (departments.length === 1) {
    return departments[0];
  }
  return defaultDepartment;
}

function buildTitle(note: string): string {
  const firstLine = note.split(/\r?\n/).find((line) => line.trim()) || note;
  const cleaned = firstLine.split(/\s+/).join(" ").trim();
  return cleaned.length > 80 ? `${cleaned.slice(0, 77)}...` : cleaned;
}
