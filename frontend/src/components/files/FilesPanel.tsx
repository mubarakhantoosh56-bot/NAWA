"use client";

import { useEffect, useMemo, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { listFiles } from "@/lib/api/files";
import type { CompanyFile, Department } from "@/lib/types";

type FilesPanelProps = {
  token: string;
  departments: Department[];
};

export function FilesPanel({ token, departments }: FilesPanelProps) {
  const [files, setFiles] = useState<CompanyFile[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState<string | null>(null);

  const departmentNames = useMemo(() => {
    return departments.reduce<Record<string, string>>((current, department) => {
      current[department.id] = department.name;
      return current;
    }, {});
  }, [departments]);

  useEffect(() => {
    let isMounted = true;

    async function loadFiles() {
      setStatus("loading");
      setError(null);
      try {
        const response = await listFiles(token);
        if (!isMounted) {
          return;
        }
        setFiles(response.files);
        setStatus("ready");
      } catch (caught) {
        if (!isMounted) {
          return;
        }
        setFiles([]);
        setStatus("error");
        setError(caught instanceof ApiError ? caught.detail : "Unable to load files.");
      }
    }

    loadFiles();

    return () => {
      isMounted = false;
    };
  }, [token]);

  async function refreshFiles() {
    setError(null);
    try {
      const response = await listFiles(token);
      setFiles(response.files);
      setStatus("ready");
    } catch (caught) {
      setStatus("error");
      setError(caught instanceof ApiError ? caught.detail : "Unable to refresh files.");
    }
  }

  return (
    <aside className="panel overflow-hidden">
      <div className="border-b border-line px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase text-muted">Company knowledge</div>
            <h2 className="mt-1 text-base font-semibold text-ink">Knowledge files</h2>
          </div>
          <button
            className="button-secondary px-2.5 py-1.5 text-xs"
            type="button"
            onClick={refreshFiles}
            disabled={status === "loading"}
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="max-h-[520px] space-y-3 overflow-y-auto bg-white p-4">
        {status === "loading" ? (
          <div className="rounded-md border border-line bg-surface p-3 text-sm text-muted">
            <span className="inline-flex items-center gap-2">
              <span className="h-2 w-2 animate-pulse rounded-full bg-accent" />
              Loading company knowledge...
            </span>
            <div className="mt-3 space-y-2">
              <div className="h-2 w-4/5 rounded bg-slate-200" />
              <div className="h-2 w-2/3 rounded bg-slate-200" />
            </div>
          </div>
        ) : null}

        {status === "error" ? (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        {status === "ready" && files.length === 0 ? (
          <div className="rounded-md border border-dashed border-line bg-surface p-3">
            <div className="text-sm font-medium text-ink">No knowledge files yet</div>
            <p className="mt-1 text-sm leading-6 text-muted">
              Seed demo files or ingest company knowledge through the backend to make
              NAWA answers more grounded.
            </p>
            <div className="mt-3 rounded-md border border-line bg-white px-3 py-2 text-xs text-muted">
              Demo hint: seeded Atlas files will appear here after the demo bootstrap script runs.
            </div>
          </div>
        ) : null}

        {files.map((file) => (
          <FileRow
            key={file.id}
            file={file}
            departmentName={file.department_id ? departmentNames[file.department_id] : null}
          />
        ))}
      </div>
    </aside>
  );
}

function FileRow({
  file,
  departmentName,
}: {
  file: CompanyFile;
  departmentName: string | null;
}) {
  return (
    <article className="rounded-md border border-line bg-white p-3 shadow-panel transition hover:border-slate-300">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 gap-2">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-line bg-surface text-[11px] font-semibold text-muted">
            DOC
          </span>
          <div className="min-w-0">
          <div className="truncate text-sm font-medium text-ink" title={file.filename}>
            {file.filename}
          </div>
          <div className="mt-1 text-xs text-muted">
            {departmentName || "Company-wide"} - {formatBytes(file.file_size_bytes)}
          </div>
          </div>
        </div>
        <StatusBadge status={file.status} />
      </div>
      <div className="mt-2 text-xs text-muted">Added {formatDate(file.created_at)}</div>
    </article>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const toneClass =
    normalized === "ready" || normalized === "processed"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : normalized === "failed" || normalized === "error"
        ? "border-red-200 bg-red-50 text-red-700"
        : normalized === "processing" || normalized === "uploaded"
          ? "border-amber-200 bg-amber-50 text-amber-700"
          : "border-line bg-surface text-muted";

  return (
    <span className={`shrink-0 rounded border px-2 py-1 text-xs capitalize ${toneClass}`}>
      {status}
    </span>
  );
}

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** index;
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "recently";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
