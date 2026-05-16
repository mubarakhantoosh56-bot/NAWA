"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { sendChatMessage } from "@/lib/api/chat";
import type { ChatResponse, Department } from "@/lib/types";

type ChatTurn = {
  id: string;
  userMessage: string;
  response: ChatResponse;
};

type ChatPanelProps = {
  token: string;
  companyId: string;
  workspaceKey: string;
  title: string;
  department: Department | null;
};

export function ChatPanel({
  token,
  companyId,
  workspaceKey,
  title,
  department,
}: ChatPanelProps) {
  const [draft, setDraft] = useState("");
  const [turnsByWorkspace, setTurnsByWorkspace] = useState<Record<string, ChatTurn[]>>({});
  const [hasLoadedSession, setHasLoadedSession] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const turns = turnsByWorkspace[workspaceKey] ?? [];
  const sessionId = useMemo(() => `frontend-${workspaceKey}-session`, [workspaceKey]);
  const storageKey = useMemo(() => `nawa.chat.${companyId}`, [companyId]);
  const suggestedPrompts = useMemo(() => getSuggestedPrompts(department), [department]);
  const workspaceLabel = department ? department.name : "CEO";

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(storageKey);
      if (saved) {
        setTurnsByWorkspace(JSON.parse(saved) as Record<string, ChatTurn[]>);
      }
    } catch {
      setTurnsByWorkspace({});
    } finally {
      setHasLoadedSession(true);
    }
  }, [storageKey]);

  useEffect(() => {
    if (!hasLoadedSession) {
      return;
    }

    window.localStorage.setItem(storageKey, JSON.stringify(turnsByWorkspace));
  }, [hasLoadedSession, storageKey, turnsByWorkspace]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || isSending) {
      return;
    }

    setDraft("");
    setError(null);
    setIsSending(true);

    try {
      const response = await sendChatMessage(token, {
        company_id: companyId,
        session_id: sessionId,
        message,
        context: buildChatContext(department),
        ...(department ? { department_id: department.id } : {}),
      });

      const nextTurn: ChatTurn = {
        id: `${workspaceKey}-${Date.now()}`,
        userMessage: message,
        response,
      };

      setTurnsByWorkspace((current) => ({
        ...current,
        [workspaceKey]: [...(current[workspaceKey] ?? []), nextTurn],
      }));
    } catch (caught) {
      setDraft(message);
      setError(caught instanceof ApiError ? caught.detail : "Unable to send message.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="panel flex min-h-[640px] flex-col overflow-hidden">
      <div className="border-b border-line bg-white px-4 py-3">
        <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
          <div className="min-w-0">
            <div className="executive-label">AI chat</div>
            <h2 className="mt-1 truncate text-base font-semibold text-ink">{title}</h2>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-muted">
            <span className="nawa-badge">
              {workspaceLabel} session
            </span>
            <span className="nawa-badge">
              Saved locally
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto bg-surface/70 p-4">
        {turns.length === 0 ? (
          <WelcomeState
            department={department}
            prompts={suggestedPrompts}
            onSelectPrompt={setDraft}
          />
        ) : null}

        {turns.map((turn) => (
          <article key={turn.id} className="space-y-3.5">
            <div className="ml-auto max-w-[88%] rounded-md border border-accent/15 bg-accent/10 p-3">
              <div className="text-xs font-semibold uppercase text-accent">You</div>
              <p className="mt-1 text-sm leading-6 text-ink">{turn.userMessage}</p>
            </div>
            <div className="max-w-[94%] rounded-md border border-line bg-white p-4 shadow-panel">
              <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
                <div className="min-w-0">
                  <div className="text-xs font-semibold uppercase text-muted">NAWA</div>
                  <p className="mt-2 whitespace-pre-wrap text-[15px] leading-7 text-ink">
                    {turn.response.ceo_text || "NAWA returned an empty summary."}
                  </p>
                </div>
                <MetaIndicators response={turn.response} />
              </div>
              <LogicPanel logic={turn.response.logic_json} />
            </div>
          </article>
        ))}

        {isSending ? (
          <div className="max-w-[94%] rounded-md border border-line bg-white p-4 text-sm text-muted shadow-panel">
            <span className="inline-flex items-center gap-2">
              <span className="h-2 w-2 animate-pulse rounded-full bg-accent" />
              NAWA is reading context and preparing a tenant-scoped answer...
            </span>
            <div className="mt-3 space-y-2">
              <div className="h-2 w-4/5 rounded bg-slate-200" />
              <div className="h-2 w-3/5 rounded bg-slate-200" />
            </div>
          </div>
        ) : null}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-line bg-white p-4">
        {error ? (
          <div className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        ) : null}
        <div className="flex flex-col gap-3 md:flex-row">
          <textarea
            className="input min-h-24 resize-none leading-6 md:min-h-16"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask NAWA for a decision, plan, or department-specific recommendation..."
            disabled={isSending}
          />
          <button className="button-primary md:w-28" type="submit" disabled={isSending || !draft.trim()}>
            {isSending ? "Sending" : "Send"}
          </button>
        </div>
        <div className="mt-2 text-xs text-muted">
          Demo hint: prompt cards fill the composer so you can review before sending.
        </div>
      </form>
    </section>
  );
}

function WelcomeState({
  department,
  prompts,
  onSelectPrompt,
}: {
  department: Department | null;
  prompts: string[];
  onSelectPrompt: (prompt: string) => void;
}) {
  const isCeo = department === null;

  return (
    <div className="rounded-md border border-dashed border-line bg-surface p-4">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_240px] lg:items-start">
        <div>
          <div className="inline-flex rounded-md border border-line bg-white px-2.5 py-1 text-xs font-semibold uppercase text-muted">
            {isCeo ? "CEO command center" : `${department.name} workspace`}
          </div>
          <h3 className="mt-3 text-lg font-semibold text-ink">
            {isCeo ? "Welcome to the NAWA executive briefing room" : "Start a department-specific briefing"}
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
            {isCeo
              ? "Ask for priorities, risks, and cross-department decisions. NAWA will keep retrieved company knowledge internal and return the current response contract."
              : "Ask this AI worker for focused recommendations using the active department context and company knowledge."}
          </p>
        </div>
        <div className="rounded-md border border-line bg-white p-3 text-xs leading-5 text-muted">
          Demo helper: choose a prompt, send it, then expand decision logic to show structured reasoning without exposing prompts or tokens.
        </div>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {prompts.map((prompt, index) => (
          <button
            key={prompt}
            className="rounded-md border border-line bg-white p-3 text-left transition hover:border-accent hover:bg-blue-50"
            type="button"
            onClick={() => onSelectPrompt(prompt)}
          >
            <span className="executive-label">
              Prompt {index + 1}
            </span>
            <span className="mt-1 block text-sm leading-5 text-ink">{prompt}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function MetaIndicators({ response }: { response: ChatResponse }) {
  return (
    <div className="flex shrink-0 flex-wrap gap-1.5 text-xs">
      <Badge tone={response.meta.parse_ok ? "good" : "warn"}>
        parse {response.meta.parse_ok ? "ok" : "check"}
      </Badge>
      <Badge tone={response.meta.memory_injected ? "good" : "neutral"}>
        memory {response.meta.memory_injected ? "on" : "off"}
      </Badge>
      <Badge tone="neutral">{response.meta.events_count} events</Badge>
    </div>
  );
}

function LogicPanel({ logic }: { logic: Record<string, unknown> }) {
  const keys = Object.keys(logic);

  return (
    <details className="mt-4 rounded-md border border-line bg-surface">
      <summary className="flex cursor-pointer items-center justify-between gap-3 px-3 py-2 text-xs font-semibold uppercase text-muted">
        <span>Decision logic</span>
        <span className="rounded border border-line bg-white px-2 py-0.5 text-[11px] normal-case text-accent">
          {keys.length ? `${keys.length} fields` : "empty"}
        </span>
      </summary>
      <pre className="max-h-56 overflow-auto border-t border-line bg-white p-3 text-xs leading-5 text-ink">
        {JSON.stringify(logic, null, 2)}
      </pre>
    </details>
  );
}

function Badge({
  tone,
  children,
}: {
  tone: "good" | "neutral" | "warn";
  children: React.ReactNode;
}) {
  const toneClass =
    tone === "good"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : tone === "warn"
        ? "border-amber-200 bg-amber-50 text-amber-700"
        : "border-line bg-surface text-muted";

  return <span className={`rounded border px-2 py-1 ${toneClass}`}>{children}</span>;
}

function buildChatContext(department: Department | null): Record<string, unknown> {
  return {
    stage: "Growing SME",
    industry: "Retail and light distribution",
    resources: "Tenant-scoped NAWA workspace",
    ...(department
      ? {
          active_workspace: department.slug,
        }
      : {
          active_workspace: "ceo",
        }),
  };
}

function getSuggestedPrompts(department: Department | null): string[] {
  if (!department) {
    return [
      "Give me the CEO briefing for this week: risks, priorities, and recommended actions.",
      "What should Atlas Home Supplies focus on before a NAWA investor demo?",
      "Summarize the top cross-department decisions we should make today.",
      "Review company knowledge and suggest a 30-day operating plan.",
    ];
  }

  const promptGroups: Record<string, string[]> = {
    sales_ai: [
      "Summarize the sales pipeline and highlight the best next actions.",
      "Which customer segments should Sales prioritize this month?",
      "Draft a practical plan to improve close rate using company knowledge.",
      "What should Sales report to the CEO before the demo?",
    ],
    finance_ai: [
      "Give me a finance briefing with cash, margin, and spending risks.",
      "Which costs should Finance review before the next planning meeting?",
      "Summarize financial priorities for the next 30 days.",
      "What finance questions should the CEO ask today?",
    ],
    marketing_ai: [
      "Summarize current marketing priorities and campaign opportunities.",
      "Which messages should Marketing emphasize for growth this month?",
      "Draft a compact campaign plan using company knowledge.",
      "What marketing proof points should we show in an investor demo?",
    ],
  };

  return (
    promptGroups[department.department_type] ?? [
      `Summarize ${department.name} priorities and recommended next actions.`,
      `What should ${department.name} report to the CEO this week?`,
      `Identify risks and blockers for ${department.name}.`,
      `Create a 30-day execution plan for ${department.name}.`,
    ]
  );
}
