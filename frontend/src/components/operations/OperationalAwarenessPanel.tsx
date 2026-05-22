"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";

import { useLanguage } from "@/components/i18n/LanguageProvider";
import { listOperationalEvents } from "@/lib/api/operational-events";
import { listSituations } from "@/lib/api/situations";
import type { OperationalEvent, OperationalSituation } from "@/lib/types";

type OperationalAwarenessPanelProps = {
  token: string;
  refreshKey: number;
};

type LoadStatus = "idle" | "loading" | "ready" | "error";

export function OperationalAwarenessPanel({ token, refreshKey }: OperationalAwarenessPanelProps) {
  const { t } = useLanguage();
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
  const missingHints = useMemo(
    () => buildMissingInformationHints(needsClassification, t),
    [needsClassification, t],
  );

  return (
    <section className="panel p-4">
      <div className="flex flex-col justify-between gap-3 border-b border-line pb-3 sm:flex-row sm:items-start">
        <div>
          <div className="executive-label">{t("operations.awareness.label")}</div>
          <h2 className="mt-1 text-base font-semibold text-ink">{t("operations.awareness.title")}</h2>
          <p className="mt-1 text-sm leading-6 text-muted">
            {t("operations.awareness.description")}
          </p>
        </div>
        <span className="rounded-md border border-line bg-surface px-2.5 py-1.5 text-xs text-muted">
          {status === "loading" ? t("common.refreshing") : t("common.readOnly")}
        </span>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <AwarenessSection title={t("operations.awareness.recentEvents")}>
          {events.length === 0 ? (
            <EmptyLine text={status === "error" ? t("operations.awareness.unableEvents") : t("operations.awareness.emptyEvents")} />
          ) : (
            events.slice(0, 5).map((event) => <EventLine key={event.id} event={event} />)
          )}
        </AwarenessSection>

        <AwarenessSection title={t("operations.awareness.needsClassification")}>
          {needsClassification.length === 0 ? (
            <EmptyLine text={t("operations.awareness.emptyClassification")} />
          ) : (
            needsClassification.slice(0, 4).map((event) => (
              <div key={event.id} className="rounded-md border border-line bg-surface px-3 py-2">
                <div className="text-xs font-semibold uppercase text-muted">{t("operations.awareness.needsClassification")}</div>
                <div className="mt-1 text-sm text-ink">{event.summary}</div>
              </div>
            ))
          )}
        </AwarenessSection>

        <AwarenessSection title={t("operations.awareness.missingInformationHints")}>
          {missingHints.length === 0 ? (
            <EmptyLine text={t("operations.awareness.emptyHints")} />
          ) : (
            missingHints.slice(0, 5).map((hint) => <EmptyLine key={hint} text={hint} />)
          )}
        </AwarenessSection>

        <AwarenessSection title={t("operations.awareness.latestSituations")}>
          {situations.length === 0 ? (
            <EmptyLine text={status === "error" ? t("operations.awareness.unableSituations") : t("operations.awareness.emptySituations")} />
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

function buildMissingInformationHints(events: OperationalEvent[], t: (key: string) => string): string[] {
  const hints: string[] = [];
  for (const event of events.slice(0, 5)) {
    const text = `${event.summary} ${event.title}`.toLowerCase();
    if (!event.department_id) {
      hints.push(`${t("operations.awareness.missingDepartment")}: ${event.title}`);
    }
    if (!/(hall|قاعة|house)\s*\d+/i.test(text)) {
      hints.push(`${t("operations.awareness.missingLocation")}: ${event.title}`);
    }
    if (!/\d/.test(text)) {
      hints.push(`${t("operations.awareness.missingQuantity")}: ${event.title}`);
    }
  }
  return Array.from(new Set(hints));
}
