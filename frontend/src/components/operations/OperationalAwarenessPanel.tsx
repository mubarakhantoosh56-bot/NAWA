"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";

import { listOperationalEvents } from "@/lib/api/operational-events";
import { listSituations } from "@/lib/api/situations";
import type { OperationalEvent, OperationalSituation } from "@/lib/types";

type OperationalAwarenessPanelProps = {
  token: string;
  refreshKey: number;
};

type LoadStatus = "idle" | "loading" | "ready" | "error";

export function OperationalAwarenessPanel({ token, refreshKey }: OperationalAwarenessPanelProps) {
  const [events, setEvents] = useState<OperationalEvent[]>([]);
  const [situations, setSituations] = useState<OperationalSituation[]>([]);
  const [status, setStatus] = useState<LoadStatus>("idle");

  useEffect(() => {
    if (!token) {
      setEvents([]);
      setSituations([]);
      setStatus("idle");
      return;
    }

    let isMounted = true;
    setStatus("loading");
    Promise.all([listOperationalEvents(token, 12), listSituations(token, 5)])
      .then(([eventResponse, situationResponse]) => {
        if (!isMounted) {
          return;
        }
        setEvents(filterDairtnaEvents(eventResponse.events));
        setSituations(situationResponse.situations.slice(0, 3));
        setStatus("ready");
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setStatus("error");
      });

    return () => {
      isMounted = false;
    };
  }, [refreshKey, token]);

  const needsClassification = useMemo(
    () =>
      events.filter(
        (event) =>
          event.source_type === "natural_capture" ||
          event.metadata?.needs_classification === true,
      ),
    [events],
  );
  const missingHints = useMemo(() => buildMissingInformationHints(needsClassification), [needsClassification]);

  return (
    <section className="panel p-4">
      <div className="flex flex-col justify-between gap-3 border-b border-line pb-3 sm:flex-row sm:items-start">
        <div>
          <div className="executive-label">Operational awareness</div>
          <h2 className="mt-1 text-base font-semibold text-ink">What NAWA is absorbing</h2>
          <p className="mt-1 text-sm leading-6 text-muted">
            Recent operational signals, classification gaps, and rule-based situations from existing data only.
          </p>
        </div>
        <span className="rounded-md border border-line bg-surface px-2.5 py-1.5 text-xs text-muted">
          {status === "loading" ? "refreshing" : "read_only"}
        </span>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <AwarenessSection title="Recent events">
          {events.length === 0 ? (
            <EmptyLine text={status === "error" ? "Unable to load recent events." : "No recent Dairtna events loaded."} />
          ) : (
            events.slice(0, 5).map((event) => <EventLine key={event.id} event={event} />)
          )}
        </AwarenessSection>

        <AwarenessSection title="Needs classification">
          {needsClassification.length === 0 ? (
            <EmptyLine text="No natural notes waiting for classification." />
          ) : (
            needsClassification.slice(0, 4).map((event) => (
              <div key={event.id} className="rounded-md border border-line bg-surface px-3 py-2">
                <div className="text-xs font-semibold uppercase text-muted">Needs classification</div>
                <div className="mt-1 text-sm text-ink">{event.summary}</div>
              </div>
            ))
          )}
        </AwarenessSection>

        <AwarenessSection title="Missing information hints">
          {missingHints.length === 0 ? (
            <EmptyLine text="No obvious missing information from recent natural notes." />
          ) : (
            missingHints.slice(0, 5).map((hint) => <EmptyLine key={hint} text={hint} />)
          )}
        </AwarenessSection>

        <AwarenessSection title="Latest situations">
          {situations.length === 0 ? (
            <EmptyLine text={status === "error" ? "Unable to load situations." : "No active situations loaded."} />
          ) : (
            situations.map((situation) => (
              <div key={situation.id} className="rounded-md border border-line bg-surface px-3 py-2">
                <div className="text-xs font-semibold uppercase text-muted">
                  {situation.severity} | {situation.status} | {situation.event_count} events
                </div>
                <div className="mt-1 text-sm font-medium text-ink">{situation.title}</div>
                <div className="mt-1 text-sm text-muted">{situation.summary}</div>
              </div>
            ))
          )}
        </AwarenessSection>
      </div>
    </section>
  );
}

function AwarenessSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs font-semibold uppercase text-muted">{title}</div>
      <div className="mt-2 space-y-2">{children}</div>
    </div>
  );
}

function EventLine({ event }: { event: OperationalEvent }) {
  return (
    <div className="rounded-md border border-line bg-surface px-3 py-2">
      <div className="text-xs font-semibold uppercase text-muted">
        {event.category} | {event.priority} | {event.source_type}
      </div>
      <div className="mt-1 text-sm font-medium text-ink">{event.title}</div>
      <div className="mt-1 text-sm text-muted">{event.summary}</div>
    </div>
  );
}

function EmptyLine({ text }: { text: string }) {
  return <div className="rounded-md border border-line bg-surface px-3 py-2 text-sm text-muted">{text}</div>;
}

function filterDairtnaEvents(events: OperationalEvent[]): OperationalEvent[] {
  return events
    .filter((event) => {
      const division = String(event.metadata?.division || event.payload?.division || "").toLowerCase();
      const text = `${event.event_type} ${event.category} ${event.title} ${event.summary}`.toLowerCase();
      return division.includes("dairtna") || text.includes("dairtna");
    })
    .slice(0, 8);
}

function buildMissingInformationHints(events: OperationalEvent[]): string[] {
  const hints: string[] = [];
  for (const event of events.slice(0, 5)) {
    const text = `${event.summary} ${event.title}`.toLowerCase();
    if (!event.department_id) {
      hints.push(`Department context missing: ${event.title}`);
    }
    if (!/(hall|قاع|house)\s*\d+/i.test(text)) {
      hints.push(`Hall or location not captured: ${event.title}`);
    }
    if (!/\d/.test(text)) {
      hints.push(`No quantity or count captured: ${event.title}`);
    }
  }
  return Array.from(new Set(hints));
}
