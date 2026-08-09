"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { sendChatMessage } from "@/lib/api/chat";
import { useLanguage } from "@/components/i18n/LanguageProvider";
import { getDemoChatTurns } from "@/lib/demo-data";
import { isDemoModeEnabled } from "@/lib/demo-mode";
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
  const { language, t } = useLanguage();
  const [draft, setDraft] = useState("");
  const [turnsByWorkspace, setTurnsByWorkspace] = useState<Record<string, ChatTurn[]>>({});
  const [hasLoadedSession, setHasLoadedSession] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const turns = turnsByWorkspace[workspaceKey] ?? [];
  const demoTurns = useMemo(
    () => (isDemoModeEnabled() ? getDemoChatTurns(department) : []),
    [department],
  );
  const isShowingDemoTurns = turns.length === 0 && demoTurns.length > 0;
  const visibleTurns = turns.length > 0 ? turns : demoTurns;
  const sessionId = useMemo(() => `frontend-${workspaceKey}-session`, [workspaceKey]);
  const storageKey = useMemo(() => `nawa.chat.${companyId}`, [companyId]);
  const suggestedPrompts = useMemo(() => getSuggestedPrompts(department, language), [department, language]);
  const workspaceLabel = department ? localizeDepartmentName(department.name, language) : "CEO";

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
        context: buildChatContext(department, language),
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
      setError(caught instanceof ApiError ? caught.detail : t("unableSendMessage"));
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="panel flex min-h-[640px] flex-col overflow-hidden">
      <div className="border-b border-line bg-white px-4 py-3">
        <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
          <div className="min-w-0">
            <div className="executive-label">{t("aiChat")}</div>
            <h2 className="mt-1 truncate text-base font-semibold text-ink">{title}</h2>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-muted">
            <span className="nawa-badge">
              {workspaceLabel} {t("session")}
            </span>
            <span className="nawa-badge">
              {turns.length > 0 ? t("savedLocally") : isShowingDemoTurns ? t("demoHistory") : t("newSession")}
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto bg-surface/70 p-4">
        {isShowingDemoTurns ? (
          <div className="rounded-md border border-amber-300 bg-amber-50 p-3">
            <div className="text-sm font-semibold text-amber-800">{t("demoDataBadge")}</div>
            <p className="mt-1 text-sm leading-6 text-amber-700">{t("demoConversationBannerText")}</p>
          </div>
        ) : null}

        {visibleTurns.length === 0 ? (
          <WelcomeState
            department={department}
            prompts={suggestedPrompts}
            onSelectPrompt={setDraft}
          />
        ) : null}

        {visibleTurns.map((turn) => (
          <article key={turn.id} className="space-y-3.5">
            <div className="ms-auto max-w-[88%] rounded-md border border-accent/15 bg-accent/10 p-3">
              <div className="text-xs font-semibold uppercase text-accent">{t("you")}</div>
              <p className="mt-1 text-sm leading-6 text-ink">{turn.userMessage}</p>
            </div>
            <div className="max-w-[94%] rounded-md border border-line bg-white p-4 shadow-panel">
              <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
                <div className="min-w-0">
                  <div className="text-xs font-semibold uppercase text-muted">NAWA</div>
                  <p className="mt-2 whitespace-pre-wrap text-[15px] leading-7 text-ink">
                    {localizeChatText(turn.response.ceo_text, language) || t("emptySummary")}
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
              {t("readingContext")}
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
            placeholder={t("askPlaceholder")}
            disabled={isSending}
          />
          <button className="button-primary md:w-28" type="submit" disabled={isSending || !draft.trim()}>
            {isSending ? t("sending") : t("send")}
          </button>
        </div>
        {isDemoModeEnabled() ? <div className="mt-2 text-xs text-muted">{t("demoHint")}</div> : null}
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
  const { language, t } = useLanguage();
  const isCeo = department === null;

  return (
    <div className="rounded-md border border-dashed border-line bg-surface p-4">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_240px] lg:items-start">
        <div>
          <div className="inline-flex rounded-md border border-line bg-white px-2.5 py-1 text-xs font-semibold uppercase text-muted">
            {isCeo ? t("ceoCommandCenter") : `${localizeDepartmentName(department.name, language)} ${t("departmentWorkspace")}`}
          </div>
          <h3 className="mt-3 text-lg font-semibold text-ink">
            {isCeo ? t("welcomeCeo") : t("welcomeDepartment")}
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
            {isCeo ? t("welcomeCeoText") : t("welcomeDepartmentText")}
          </p>
        </div>
        {isDemoModeEnabled() ? (
          <div className="rounded-md border border-line bg-white p-3 text-xs leading-5 text-muted">
            {t("demoHelper")}
          </div>
        ) : null}
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {prompts.map((prompt, index) => (
          <button
            key={prompt}
            className="rounded-md border border-line bg-white p-3 text-start transition hover:border-accent hover:bg-blue-50"
            type="button"
            onClick={() => onSelectPrompt(prompt)}
          >
            <span className="executive-label">
              {t("prompt")} {index + 1}
            </span>
            <span className="mt-1 block text-sm leading-5 text-ink">{prompt}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function MetaIndicators({ response }: { response: ChatResponse }) {
  const { t } = useLanguage();

  return (
    <div className="flex shrink-0 flex-wrap gap-1.5 text-xs">
      <Badge tone={response.meta.parse_ok ? "good" : "warn"}>
        {t("parse")} {response.meta.parse_ok ? t("ok") : t("check")}
      </Badge>
      <Badge tone={response.meta.memory_injected ? "good" : "neutral"}>
        {t("memory")} {response.meta.memory_injected ? t("on") : t("off")}
      </Badge>
      <Badge tone="neutral">
        {response.meta.events_count} {t("events")}
      </Badge>
    </div>
  );
}

function LogicPanel({ logic }: { logic: Record<string, unknown> }) {
  const { t } = useLanguage();
  const keys = Object.keys(logic);

  return (
    <details className="mt-4 rounded-md border border-line bg-surface">
      <summary className="flex cursor-pointer items-center justify-between gap-3 px-3 py-2 text-xs font-semibold uppercase text-muted">
        <span>{t("decisionLogic")}</span>
        <span className="rounded border border-line bg-white px-2 py-0.5 text-[11px] normal-case text-accent">
          {keys.length ? `${keys.length} ${t("fields")}` : t("empty")}
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

function buildChatContext(department: Department | null, language: "en" | "ar"): Record<string, unknown> {
  return {
    stage: "Enterprise expansion",
    industry: "Commercial services and supply operations",
    resources: "Tenant-scoped NAWA workspace",
    response_language: language,
    ui_language: language,
    ...(department
      ? {
          active_workspace: department.slug,
        }
      : {
          active_workspace: "ceo",
        }),
  };
}

function getSuggestedPrompts(department: Department | null, language: "en" | "ar"): string[] {
  if (!department) {
    const prompts = [
      "Give me the CEO briefing for this week: risks, priorities, and recommended actions.",
      "What should Northstar focus on before a NAWA investor demo?",
      "Summarize the top cross-department decisions we should make today.",
      "Review company knowledge and suggest a 30-day operating plan.",
    ];
    return language === "ar" ? prompts.map(localizePrompt) : prompts;
  }

  const promptGroups: Record<string, string[]> = {
    sales_ai: [
      "Summarize the sales pipeline and highlight the best next actions.",
      "Which expansion accounts should Sales prioritize this month?",
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

  const prompts =
    promptGroups[department.department_type] ?? [
      `Summarize ${department.name} priorities and recommended next actions.`,
      `What should ${department.name} report to the CEO this week?`,
      `Identify risks and blockers for ${department.name}.`,
      `Create a 30-day execution plan for ${department.name}.`,
    ];

  return language === "ar" ? prompts.map(localizePrompt) : prompts;
}

function localizeDepartmentName(value: string, language: "en" | "ar"): string {
  if (language === "en") {
    return value;
  }

  const names: Record<string, string> = {
    CEO: "الإدارة التنفيذية",
    Sales: "المبيعات",
    Finance: "المالية",
    Marketing: "التسويق",
    Operations: "العمليات",
  };
  return names[value] || value;
}

function localizePrompt(value: string): string {
  const prompts: Record<string, string> = {
    "Give me the CEO briefing for this week: risks, priorities, and recommended actions.":
      "أعطني إحاطة CEO لهذا الأسبوع: المخاطر، الأولويات، والإجراءات المقترحة.",
    "What should Northstar focus on before a NAWA investor demo?":
      "ما الذي يجب أن تركز عليه Northstar قبل عرض NAWA للمستثمرين؟",
    "Summarize the top cross-department decisions we should make today.":
      "لخص أهم القرارات المشتركة بين الأقسام التي يجب اتخاذها اليوم.",
    "Review company knowledge and suggest a 30-day operating plan.":
      "راجع معرفة الشركة واقترح خطة تشغيل لمدة 30 يوما.",
    "Summarize the sales pipeline and highlight the best next actions.":
      "لخص pipeline المبيعات وحدد أفضل الإجراءات التالية.",
    "Which expansion accounts should Sales prioritize this month?":
      "أي حسابات توسع يجب أن تعطيها المبيعات الأولوية هذا الشهر؟",
    "Draft a practical plan to improve close rate using company knowledge.":
      "اكتب خطة عملية لتحسين معدل الإغلاق باستخدام معرفة الشركة.",
    "What should Sales report to the CEO before the demo?":
      "ما الذي يجب أن ترفعه المبيعات إلى CEO قبل العرض؟",
    "Give me a finance briefing with cash, margin, and spending risks.":
      "أعطني إحاطة مالية عن النقد والهامش ومخاطر الإنفاق.",
    "Which costs should Finance review before the next planning meeting?":
      "ما التكاليف التي يجب أن تراجعها المالية قبل اجتماع التخطيط القادم؟",
    "Summarize financial priorities for the next 30 days.":
      "لخص الأولويات المالية للـ 30 يوما القادمة.",
    "What finance questions should the CEO ask today?":
      "ما الأسئلة المالية التي يجب أن يسألها CEO اليوم؟",
    "Summarize current marketing priorities and campaign opportunities.":
      "لخص أولويات التسويق الحالية وفرص الحملات.",
    "Which messages should Marketing emphasize for growth this month?":
      "ما الرسائل التي يجب أن يركز عليها التسويق للنمو هذا الشهر؟",
    "Draft a compact campaign plan using company knowledge.":
      "اكتب خطة حملة مختصرة باستخدام معرفة الشركة.",
    "What marketing proof points should we show in an investor demo?":
      "ما نقاط الإثبات التسويقية التي يجب عرضها للمستثمرين؟",
  };

  return prompts[value] || value;
}

function localizeChatText(value: string, language: "en" | "ar"): string {
  if (language === "en") {
    return value;
  }

  const responses: Record<string, string> = {
    "Revenue quality is improving, but execution risk is shifting from demand to fulfillment capacity.\n\nRecommended decision: approve the focused expansion plan for 14 high-fit accounts, keep discounts above 8% under Finance review, and ask Operations for a weekly capacity checkpoint before Sales commits to delivery-heavy proposals.":
      "جودة الإيرادات تتحسن، لكن مخاطر التنفيذ تنتقل من الطلب إلى سعة التنفيذ.\n\nالقرار المقترح: اعتماد خطة توسع مركزة لـ 14 حسابا عالي الملاءمة، إبقاء الخصومات فوق 8% تحت مراجعة المالية، وطلب نقطة تحقق أسبوعية من العمليات قبل التزام المبيعات بعروض كثيفة التسليم.",
    "Prioritize expansion accounts with active budget, clear procurement ownership, and low delivery complexity.\n\nThe best near-term motion is a 14-account focus list: facilities management groups, multi-site offices, and hospitality operators with repeat purchasing patterns. Avoid low-margin one-off bids unless Finance approves the discount structure.":
      "أعط الأولوية لحسابات التوسع ذات الميزانية النشطة، ومالك شراء واضح، وتعقيد تسليم منخفض.\n\nأفضل حركة قريبة هي قائمة تركيز من 14 حسابا: مجموعات إدارة المرافق، المكاتب متعددة المواقع، ومشغلي الضيافة ذوي أنماط الشراء المتكررة. تجنب العروض الفردية منخفضة الهامش إلا إذا وافقت المالية على هيكل الخصم.",
    "The growth plan is financially supportable if discounting remains controlled.\n\nCash coverage is healthy at 5.8 months. The main exposure is $86K in proposed discounts across two large opportunities. Finance should approve campaign spend, but require executive review for payment terms above 30 days or discounts above 8%.":
      "خطة النمو قابلة للدعم ماليا إذا بقيت الخصومات مضبوطة.\n\nالتغطية النقدية صحية عند 5.8 أشهر. التعرض الأساسي هو 86 ألف دولار في خصومات مقترحة عبر فرصتين كبيرتين. ينبغي للمالية اعتماد إنفاق الحملات، مع طلب مراجعة تنفيذية لشروط الدفع فوق 30 يوما أو الخصومات فوق 8%.",
    "Lead with operational reliability and measurable execution outcomes.\n\nCampaigns mentioning faster replenishment, fewer service interruptions, and accountable delivery operations are outperforming generic productivity language. Shift budget toward proof-led executive campaigns and use Sales feedback to refine account-specific messaging.":
      "ابدأ برسالة الاعتمادية التشغيلية ونتائج التنفيذ القابلة للقياس.\n\nالحملات التي تذكر توريدا أسرع، وانقطاعات خدمة أقل، وعمليات تسليم مسؤولة تتفوق على لغة الإنتاجية العامة. حوّل الميزانية نحو حملات تنفيذية قائمة على الإثبات واستخدم ملاحظات المبيعات لتحسين الرسائل الخاصة بالحسابات.",
  };

  return responses[value] || value;
}
