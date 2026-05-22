"use client";

import { useCallback, useEffect, useState } from "react";

import { useLanguage } from "@/components/i18n/LanguageProvider";
import { ApiError } from "@/lib/api/client";
import { confirmDraft, getFileDrafts, rejectDraft } from "@/lib/api/files";
import type { EventDraft } from "@/lib/types";

type Props = {
  token: string;
  fileId: string;
  filename: string;
  onClose: () => void;
};

type CardStatus = "idle" | "confirming" | "rejecting" | "confirmed" | "rejected" | "error";

export function OperationalFileDraftPanel({ token, fileId, filename, onClose }: Props) {
  const { t } = useLanguage();
  const [drafts, setDrafts] = useState<EventDraft[]>([]);
  const [loadStatus, setLoadStatus] = useState<"loading" | "ready" | "error">("loading");
  const [loadError, setLoadError] = useState("");
  const [cardStatus, setCardStatus] = useState<Record<string, CardStatus>>({});

  const loadDrafts = useCallback(async () => {
    setLoadStatus("loading");
    setLoadError("");
    try {
      const response = await getFileDrafts(token, fileId);
      setDrafts(response.drafts);
      setLoadStatus("ready");
    } catch (caught) {
      setLoadStatus("error");
      setLoadError(caught instanceof ApiError ? caught.detail : t("operations.fileDraft.error"));
    }
  }, [fileId, t, token]);

  useEffect(() => {
    loadDrafts();
  }, [loadDrafts]);

  async function handleConfirm(draft: EventDraft) {
    setCardStatus((prev) => ({ ...prev, [draft.id]: "confirming" }));
    try {
      await confirmDraft(token, fileId, draft.id);
      setCardStatus((prev) => ({ ...prev, [draft.id]: "confirmed" }));
      setDrafts((prev) => prev.filter((d) => d.id !== draft.id));
    } catch {
      setCardStatus((prev) => ({ ...prev, [draft.id]: "error" }));
    }
  }

  async function handleReject(draft: EventDraft) {
    setCardStatus((prev) => ({ ...prev, [draft.id]: "rejecting" }));
    try {
      await rejectDraft(token, fileId, draft.id);
      setCardStatus((prev) => ({ ...prev, [draft.id]: "rejected" }));
      setDrafts((prev) => prev.filter((d) => d.id !== draft.id));
    } catch {
      setCardStatus((prev) => ({ ...prev, [draft.id]: "error" }));
    }
  }

  return (
    <section className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded border border-amber-300 bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
              {t("operations.fileDraft.badge")}
            </span>
            <span className="truncate text-xs text-amber-700" title={filename}>
              {filename}
            </span>
          </div>
          <h3 className="mt-1 text-sm font-semibold text-ink">{t("operations.fileDraft.title")}</h3>
          <p className="text-xs text-amber-700">{t("operations.fileDraft.subtitle")}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="shrink-0 rounded px-2 py-1 text-xs text-muted hover:text-ink"
        >
          {t("operations.fileDraft.close")}
        </button>
      </div>

      <div className="mt-3 space-y-3">
        {loadStatus === "loading" && (
          <div className="text-xs text-amber-700">{t("operations.fileDraft.loading")}</div>
        )}

        {loadStatus === "error" && (
          <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            {loadError}
          </div>
        )}

        {loadStatus === "ready" && drafts.length === 0 && (
          <div className="text-xs text-muted">{t("operations.fileDraft.empty")}</div>
        )}

        {drafts.map((draft) => (
          <DraftCard
            key={draft.id}
            draft={draft}
            status={cardStatus[draft.id] ?? "idle"}
            onConfirm={() => handleConfirm(draft)}
            onReject={() => handleReject(draft)}
            t={t}
          />
        ))}
      </div>
    </section>
  );
}

function DraftCard({
  draft,
  status,
  onConfirm,
  onReject,
  t,
}: {
  draft: EventDraft;
  status: CardStatus;
  onConfirm: () => void;
  onReject: () => void;
  t: (key: string) => string;
}) {
  const busy = status === "confirming" || status === "rejecting";

  return (
    <article className="rounded-md border border-amber-200 bg-white p-3 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <CategoryBadge category={draft.proposed_category} t={t} />
        <PriorityBadge priority={draft.proposed_priority} />
        <ConfidenceBadge confidence={draft.confidence} t={t} />
      </div>

      {draft.needs_clarification && (
        <div className="mt-2 rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800">
          {t("operations.fileDraft.needsClarification")}
        </div>
      )}

      <p className="mt-2 text-sm font-medium text-ink">{draft.proposed_title}</p>
      <p className="mt-1 text-xs leading-5 text-muted">{draft.proposed_summary}</p>

      {draft.evidence_quote && (
        <blockquote className="mt-2 border-s-2 border-amber-300 ps-2 text-xs italic text-muted">
          <span className="not-italic font-medium text-muted">{t("operations.fileDraft.evidence")}: </span>
          {draft.evidence_quote}
        </blockquote>
      )}

      {status === "error" && (
        <div className="mt-2 text-xs text-red-600">{t("operations.fileDraft.actionError")}</div>
      )}

      <div className="mt-3 flex gap-2">
        <button
          type="button"
          className="button-primary px-3 py-1.5 text-xs"
          disabled={busy}
          onClick={onConfirm}
        >
          {status === "confirming" ? t("operations.fileDraft.confirming") : t("operations.fileDraft.confirm")}
        </button>
        <button
          type="button"
          className="button-secondary px-3 py-1.5 text-xs"
          disabled={busy}
          onClick={onReject}
        >
          {status === "rejecting" ? t("operations.fileDraft.rejecting") : t("operations.fileDraft.reject")}
        </button>
      </div>
    </article>
  );
}

function CategoryBadge({ category, t }: { category: string; t: (key: string) => string }) {
  const label = t(`operations.input.categories.${category}`) || category;
  return (
    <span className="rounded border border-line bg-surface px-2 py-0.5 text-xs text-muted">
      {label}
    </span>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  const toneClass =
    priority === "critical"
      ? "border-red-200 bg-red-50 text-red-700"
      : priority === "high"
        ? "border-orange-200 bg-orange-50 text-orange-700"
        : priority === "watch"
          ? "border-amber-200 bg-amber-50 text-amber-700"
          : "border-line bg-surface text-muted";

  return (
    <span className={`rounded border px-2 py-0.5 text-xs capitalize ${toneClass}`}>
      {priority}
    </span>
  );
}

function ConfidenceBadge({ confidence, t }: { confidence: number; t: (key: string) => string }) {
  const toneClass =
    confidence >= 80
      ? "text-emerald-700"
      : confidence >= 50
        ? "text-amber-700"
        : "text-red-600";

  return (
    <span className={`text-xs ${toneClass}`}>
      {t("operations.fileDraft.confidence")}: {confidence}/100
    </span>
  );
}
