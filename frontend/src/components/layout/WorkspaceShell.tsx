"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { FilesPanel } from "@/components/files/FilesPanel";
import { LanguageToggle } from "@/components/i18n/LanguageToggle";
import { useLanguage } from "@/components/i18n/LanguageProvider";
import { ApiError } from "@/lib/api/client";
import { listDepartments } from "@/lib/api/departments";
import {
  DEMO_COMPANY,
  DEMO_DEPARTMENTS,
  DEMO_EXECUTIVE_SUMMARIES,
  DEMO_KPIS,
  DEMO_REPORTS,
  getDemoWorkspaceKey,
} from "@/lib/demo-data";
import type { Language } from "@/lib/i18n";
import type { Department } from "@/lib/types";

type ActiveWorkspace =
  | {
      kind: "ceo";
    }
  | {
      kind: "department";
      departmentId: string;
    };

const departmentTypeLabels: Record<string, string> = {
  sales_ai: "Sales AI",
  finance_ai: "Finance AI",
  marketing_ai: "Marketing AI",
  hr_ai: "HR AI",
  operations_ai: "Operations AI",
  warehouse_ai: "Warehouse AI",
  production_ai: "Production AI",
  custom: "Department AI",
};

const departmentTypeBadges: Record<string, string> = {
  sales_ai: "SA",
  finance_ai: "FA",
  marketing_ai: "MA",
  hr_ai: "HR",
  operations_ai: "OP",
  warehouse_ai: "WH",
  production_ai: "PR",
  custom: "AI",
};

export function WorkspaceShell() {
  const { me, token, logout } = useAuth();
  const { language, t } = useLanguage();
  const permissions = me?.role.permissions ?? [];
  const [departments, setDepartments] = useState<Department[]>([]);
  const [departmentStatus, setDepartmentStatus] = useState<"idle" | "loading" | "ready" | "blocked" | "error">(
    "idle",
  );
  const [departmentError, setDepartmentError] = useState<string | null>(null);
  const [activeWorkspace, setActiveWorkspace] = useState<ActiveWorkspace>({ kind: "ceo" });

  const canReadDepartments = hasPermission(permissions, "departments.read");
  const canReadFiles = hasPermission(permissions, "files.read");

  useEffect(() => {
    if (!token || !canReadDepartments) {
      setDepartments([]);
      setDepartmentStatus(canReadDepartments ? "idle" : "blocked");
      return;
    }

    let isMounted = true;
    setDepartmentStatus("loading");
    setDepartmentError(null);

    listDepartments(token)
      .then((response) => {
        if (!isMounted) {
          return;
        }
        setDepartments(response.departments);
        setDepartmentStatus("ready");
      })
      .catch((caught) => {
        if (!isMounted) {
          return;
        }
        setDepartments([]);
        setDepartmentStatus("error");
        setDepartmentError(caught instanceof ApiError ? caught.detail : t("unableLoadDepartments"));
      });

    return () => {
      isMounted = false;
    };
  }, [canReadDepartments, t, token]);

  const displayDepartments = departments.length > 0 ? departments : DEMO_DEPARTMENTS;
  const isDemoDataset = departments.length === 0;

  const activeDepartment = useMemo(() => {
    if (activeWorkspace.kind !== "department") {
      return null;
    }
    return displayDepartments.find((department) => department.id === activeWorkspace.departmentId) ?? null;
  }, [activeWorkspace, displayDepartments]);

  const demoWorkspaceKey = getDemoWorkspaceKey(activeDepartment);
  const activeTitle = activeDepartment ? getDepartmentAgentLabel(activeDepartment, language) : t("ceoAiWorkspace");
  const activeScope = activeDepartment ? t("departmentScoped") : t("companyWide");
  const activeDescription = activeDepartment
    ? localizeDepartmentDescription(activeDepartment, language)
    : localizeWorkspaceText(
        "Company-wide AI workspace for executive planning, cross-department priorities, and demo-ready NAWA decisions.",
        language,
      );
  const activeWorkspaceKey = activeDepartment ? `department-${activeDepartment.id}` : "ceo";

  return (
    <main className="min-h-screen text-ink">
      <header className="border-b border-white/10 bg-executive text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md border border-white/15 bg-white/10 text-sm font-semibold text-white">
              N
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide text-white">{t("brandNawa")}</div>
              <div className="text-xs text-white/60">{t("aiWorkforcePlatform")}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <LanguageToggle />
            <div className="hidden text-end sm:block">
              <div className="text-sm font-medium">{me?.company.name || DEMO_COMPANY.name}</div>
              <div className="text-xs text-white/60">{me?.user.email || DEMO_COMPANY.email}</div>
            </div>
            <button
              className="rounded-md border border-white/15 bg-white/10 px-3 py-2 text-sm font-medium text-white transition hover:bg-white/15"
              type="button"
              onClick={logout}
            >
              {t("logout")}
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-4 px-4 py-4 sm:px-6 lg:grid-cols-[260px_1fr]">
        <aside className="command-panel h-fit p-3 lg:sticky lg:top-4">
          <div className="px-2 pb-2 text-xs font-semibold uppercase text-white/60">{t("workspace")}</div>
          <nav className="space-y-1">
            <SidebarItem
              label={t("ceoAi")}
              description={t("executiveCommand")}
              badge="CEO"
              active={activeWorkspace.kind === "ceo"}
              onClick={() => setActiveWorkspace({ kind: "ceo" })}
            />

            <div className="px-2 pt-3 text-xs font-semibold uppercase text-white/60">{t("departments")}</div>

            {departmentStatus === "loading" ? (
              <div className="rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/70">
                <span className="inline-flex items-center gap-2">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-gold" />
                  {t("loadingDepartments")}
                </span>
              </div>
            ) : null}

            {departmentStatus === "blocked" ? (
              <div className="rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/70">
                {t("departmentListUnavailable")}
              </div>
            ) : null}

            {departmentStatus === "error" ? (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {departmentError}
              </div>
            ) : null}

            {isDemoDataset ? (
              <div className="rounded-md border border-white/10 bg-white/5 px-3 py-2">
                <div className="text-sm font-medium text-white">{t("investorDemoDataset")}</div>
                <div className="mt-1 text-xs leading-5 text-white/55">{t("investorDemoDatasetDetail")}</div>
              </div>
            ) : null}

            {displayDepartments.map((department) => {
              const canUseDepartment = isDemoDataset || canUseAgent(permissions, department.department_type);
              return (
                <SidebarItem
                  key={department.id}
                  label={getDepartmentAgentLabel(department, language)}
                  description={localizeDepartmentName(department.name, language)}
                  badge={getDepartmentBadge(department)}
                  active={activeWorkspace.kind === "department" && activeWorkspace.departmentId === department.id}
                  disabled={!canUseDepartment || !department.ai_agent_enabled}
                  lockLabel={!canUseDepartment ? t("locked") : t("offLabel")}
                  onClick={() =>
                    setActiveWorkspace({
                      kind: "department",
                      departmentId: department.id,
                    })
                  }
                />
              );
            })}
          </nav>
          <div className="mt-4 border-t border-white/10 px-2 pt-3">
            <div className="text-xs font-semibold uppercase text-white/60">{t("role")}</div>
            <div className="mt-1 text-sm font-medium text-white">
              {localizeWorkspaceText(me?.role.name || DEMO_COMPANY.role, language)}
            </div>
            <div className="mt-1 text-xs text-white/60">
              {permissions.length} {t("permissionsAvailable")}
            </div>
          </div>
        </aside>

        <section className="space-y-4">
          <div className="command-panel p-4">
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
              <div>
                <div className="text-xs font-semibold uppercase text-white/60">{t("liveAiWorkforce")}</div>
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <h1 className="text-xl font-semibold text-white">{activeTitle}</h1>
                  <span className="rounded-md border border-white/10 bg-white/10 px-2 py-1 text-xs font-medium text-white/70">
                    {activeDepartment ? localizeDepartmentName(activeDepartment.name, language) : t("executive")}
                  </span>
                </div>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-white/70">{activeDescription}</p>
              </div>
              <div className="rounded-md border border-white/10 bg-white/10 px-3 py-2 text-xs text-white/70">
                {t("scope")}: {activeScope}
              </div>
            </div>
          </div>

          <QuickStartPanel activeTitle={activeTitle} canReadFiles={canReadFiles} />

          <div className="grid gap-3 md:grid-cols-3">
            {DEMO_KPIS[demoWorkspaceKey].map((kpi) => (
              <StatusPanel
                key={kpi.title}
                title={localizeWorkspaceText(kpi.title, language)}
                value={kpi.value}
                detail={localizeWorkspaceText(kpi.detail, language)}
              />
            ))}
          </div>

          <DemoBriefingPanel workspaceKey={demoWorkspaceKey} />

          {token && me ? (
            <div className={canReadFiles ? "grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]" : ""}>
              <ChatPanel
                token={token}
                companyId={me.company.id}
                workspaceKey={activeWorkspaceKey}
                title={activeTitle}
                department={activeDepartment}
              />
              {canReadFiles ? <FilesPanel token={token} departments={displayDepartments} /> : null}
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}

function DemoBriefingPanel({ workspaceKey }: { workspaceKey: keyof typeof DEMO_REPORTS }) {
  const { language, t } = useLanguage();

  return (
    <section className="panel p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-2xl">
          <div className="executive-label">{t("executiveSummary")}</div>
          <p className="mt-2 text-sm leading-6 text-ink">
            {localizeWorkspaceText(DEMO_EXECUTIVE_SUMMARIES[workspaceKey], language)}
          </p>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 lg:min-w-[520px]">
          {DEMO_REPORTS[workspaceKey].map((report) => (
            <article key={report.title} className="rounded-md border border-line bg-surface px-3 py-2.5">
              <div className="text-sm font-semibold text-ink">{localizeWorkspaceText(report.title, language)}</div>
              <p className="mt-1 text-xs leading-5 text-muted">{localizeWorkspaceText(report.detail, language)}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function QuickStartPanel({ activeTitle, canReadFiles }: { activeTitle: string; canReadFiles: boolean }) {
  const { t } = useLanguage();

  return (
    <section className="panel p-3">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="executive-label">{t("demoQuickStart")}</div>
          <div className="mt-1 text-sm font-medium text-ink">{t("quickStartText")}</div>
        </div>
        <div className="grid gap-2 text-xs text-muted sm:grid-cols-3 lg:min-w-[520px]">
          <QuickStartStep value="1" label={activeTitle} />
          <QuickStartStep value="2" label={canReadFiles ? t("reviewKnowledgeFiles") : t("filesLocked")} />
          <QuickStartStep value="3" label={t("useSuggestedPrompt")} />
        </div>
      </div>
    </section>
  );
}

function QuickStartStep({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex items-center gap-2 rounded-md border border-line bg-surface px-2.5 py-2">
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-accent/20 bg-white text-[11px] font-semibold text-accent">
        {value}
      </span>
      <span className="truncate">{label}</span>
    </div>
  );
}

function SidebarItem({
  label,
  description,
  badge,
  active,
  disabled = false,
  lockLabel,
  onClick,
}: {
  label: string;
  description: string;
  badge: string;
  active: boolean;
  disabled?: boolean;
  lockLabel?: string;
  onClick: () => void;
}) {
  const { direction, t } = useLanguage();

  return (
    <button
      className={`w-full rounded-md px-3 py-2 text-start text-sm transition ${
        active
          ? "bg-white/10 font-medium text-white"
          : disabled
            ? "cursor-not-allowed bg-white/5 text-white/50 opacity-70"
            : "text-white/80 hover:bg-white/10"
      }`}
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={disabled ? t("workspaceUnavailable") : undefined}
    >
      <span className={`flex items-start gap-2 ${direction === "rtl" ? "flex-row-reverse" : ""}`}>
        <span
          className={`mt-0.5 flex h-7 w-8 shrink-0 items-center justify-center rounded-md border text-[11px] font-semibold ${
            active ? "border-gold/50 bg-gold/15 text-gold" : "border-white/10 bg-white/5 text-white/60"
          }`}
        >
          {badge}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center justify-between gap-2">
            <span className="truncate">{label}</span>
            {disabled ? (
              <span className="rounded border border-line px-1.5 py-0.5 text-[10px] uppercase text-muted">
                {lockLabel || t("locked")}
              </span>
            ) : null}
          </span>
          <span className="mt-0.5 block truncate text-xs text-white/50">{description}</span>
        </span>
      </span>
    </button>
  );
}

function StatusPanel({ title, value, detail }: { title: string; value: string; detail: string }) {
  return (
    <div className="panel p-4">
      <div className="text-xs font-semibold uppercase text-muted">{title}</div>
      <div className="mt-2 text-base font-semibold text-ink">{value}</div>
      <div className="mt-1 text-sm text-muted">{detail}</div>
    </div>
  );
}

function getDepartmentAgentLabel(department: Department, language: Language): string {
  return localizeWorkspaceText(
    departmentTypeLabels[department.department_type] || `${department.name} AI`,
    language,
  );
}

function getDepartmentBadge(department: Department): string {
  return departmentTypeBadges[department.department_type] || department.name.slice(0, 2).toUpperCase();
}

function canUseAgent(permissions: string[], departmentType: string): boolean {
  return hasPermission(permissions, `agents.${departmentType}.use`);
}

function hasPermission(permissions: string[], permission: string): boolean {
  return permissions.includes("*") || permissions.includes(permission);
}

function localizeDepartmentName(value: string, language: Language): string {
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

function localizeDepartmentDescription(department: Department, language: Language): string {
  const fallback = department.description || `${department.name} workspace is ready for chat integration.`;
  if (language === "en") {
    return fallback;
  }

  const descriptions: Record<string, string> = {
    sales_ai: "ذكاء الإيرادات لجودة pipeline وتركيز الحسابات والخطوات التنفيذية.",
    finance_ai: "ذكاء مالي لمتابعة النقد والهامش وقرارات الميزانية.",
    marketing_ai: "ذكاء تسويقي لتركيز الحملات وجودة الإشارات ونقاط الإثبات.",
    operations_ai: "ذكاء تشغيلي للسعة ومخاطر الخدمة والتنفيذ الأسبوعي.",
    custom: "ذكاء تنفيذي للأولويات والقرارات المشتركة بين الأقسام.",
  };
  return descriptions[department.department_type] || fallback;
}

function localizeWorkspaceText(value: string, language: Language): string {
  if (language === "en") {
    return value;
  }

  const translations: Record<string, string> = {
    "Sales AI": "Sales AI",
    "Finance AI": "Finance AI",
    "Marketing AI": "Marketing AI",
    "Operations AI": "Operations AI",
    "HR AI": "HR AI",
    "Department AI": "Department AI",
    Owner: "المالك",
    "Executive Demo Owner": "مالك demo التنفيذي",
    "Company-wide AI workspace for executive planning, cross-department priorities, and demo-ready NAWA decisions.":
      "مساحة ذكاء على مستوى الشركة للتخطيط التنفيذي والأولويات المشتركة وقرارات NAWA الجاهزة للعرض.",
    "Revenue Run Rate": "معدل الإيراد السنوي",
    "Gross Margin": "الهامش الإجمالي",
    "Execution Risk": "مخاطر التنفيذ",
    "Qualified Pipeline": "Pipeline مؤهل",
    "Win Rate": "معدل الفوز",
    "Next Actions": "الإجراءات التالية",
    "Cash Coverage": "تغطية نقدية",
    "Discount Exposure": "تعرض الخصومات",
    "Budget Variance": "انحراف الميزانية",
    "Qualified Demand": "طلب مؤهل",
    "CAC Payback": "استرداد CAC",
    "Campaign Signal": "إشارة الحملة",
    "+11.6% quarter over quarter": "+11.6% ربعيا",
    "1.9 pts above guardrail": "أعلى من الحد بـ 1.9 نقطة",
    "Operations capacity is the constraint": "سعة العمليات هي القيد الأساسي",
    "68% tied to expansion accounts": "68% مرتبط بحسابات توسع",
    "+4 pts after account segmentation": "+4 نقاط بعد تقسيم الحسابات",
    "CEO-ready follow-ups due this week": "متابعات جاهزة للـ CEO هذا الأسبوع",
    "Healthy with controlled hiring": "صحية مع توظيف مضبوط",
    "Two deals require approval": "صفقتان تحتاجان موافقة",
    "Below plan after vendor renegotiation": "أقل من الخطة بعد إعادة التفاوض",
    "High-intent accounts this month": "حسابات عالية النية هذا الشهر",
    "Improved by 1.4 months": "تحسن بـ 1.4 شهر",
    "Operations proof points outperform": "نقاط إثبات العمليات تتفوق",
    "Northstar is ready to accelerate, but the next phase should be governed by fulfillment capacity, margin protection, and account-level focus.":
      "Northstar جاهزة للتسارع، لكن المرحلة التالية يجب أن تُدار بسعة التنفيذ وحماية الهامش وتركيز الحسابات.",
    "Sales should concentrate on expansion accounts with budget authority and low operational drag, then escalate only margin-sensitive deals.":
      "على المبيعات التركيز على حسابات التوسع ذات صلاحية الميزانية والأثر التشغيلي المنخفض، مع تصعيد الصفقات الحساسة للهامش فقط.",
    "Finance can support the growth plan while preserving cash coverage, provided discounting and procurement commitments remain governed.":
      "يمكن للمالية دعم خطة النمو مع الحفاظ على التغطية النقدية إذا بقيت الخصومات والتزامات الشراء محكومة.",
    "Marketing should lead with operational reliability, measurable execution outcomes, and proof from high-fit commercial accounts.":
      "على التسويق قيادة الرسالة بالاعتمادية التشغيلية ونتائج التنفيذ القابلة للقياس وإثباتات الحسابات الملائمة.",
    "Executive Operating Brief": "إحاطة تشغيلية تنفيذية",
    "Board Narrative": "سردية مجلس الإدارة",
    "Pipeline Quality Review": "مراجعة جودة pipeline",
    "Account Focus Plan": "خطة تركيز الحسابات",
    "Margin Guardrail Report": "تقرير حدود الهامش",
    "Cash Discipline Memo": "مذكرة الانضباط النقدي",
    "Campaign Signal Review": "مراجعة إشارات الحملة",
    "Demand Generation Brief": "إحاطة توليد الطلب",
    "Revenue growth remains healthy; fulfillment capacity is now the highest leverage decision.":
      "نمو الإيرادات صحي؛ سعة التنفيذ هي الآن قرار الرافعة الأعلى.",
    "Northstar is shifting from opportunistic growth to governed, repeatable execution.":
      "تنتقل Northstar من نمو انتهازي إلى تنفيذ محكوم وقابل للتكرار.",
    "Enterprise services and facilities accounts show the best margin-adjusted conversion.":
      "حسابات الخدمات المؤسسية والمرافق تظهر أفضل تحويل معدل بالهامش.",
    "Prioritize 14 accounts with active budget, low delivery complexity, and renewal urgency.":
      "الأولوية لـ 14 حسابا بميزانية نشطة وتعقيد تسليم منخفض وإلحاح تجديد.",
    "Finance should approve growth spend, but hold discounts above 8% for executive review.":
      "ينبغي للمالية اعتماد إنفاق النمو مع إبقاء الخصومات فوق 8% للمراجعة التنفيذية.",
    "Working capital remains stable if procurement stays inside the approved replenishment model.":
      "يبقى رأس المال العامل مستقرا إذا بقي الشراء ضمن نموذج التوريد المعتمد.",
    "Operational reliability messaging is outperforming generic productivity language.":
      "رسائل الاعتمادية التشغيلية تتفوق على لغة الإنتاجية العامة.",
    "Shift spend toward proof-led executive campaigns and reduce broad awareness placements.":
      "حوّل الإنفاق نحو حملات تنفيذية قائمة على الإثبات وقلل الظهور العام.",
  };

  return translations[value] || value;
}
