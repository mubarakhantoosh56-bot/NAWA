"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { FilesPanel } from "@/components/files/FilesPanel";
import { LanguageToggle } from "@/components/i18n/LanguageToggle";
import { useLanguage } from "@/components/i18n/LanguageProvider";
import { ManualOperationalEventPanel } from "@/components/operations/ManualOperationalEventPanel";
import { NaturalOperationalCapturePanel } from "@/components/operations/NaturalOperationalCapturePanel";
import { OperationalAwarenessPanel } from "@/components/operations/OperationalAwarenessPanel";
import { OperationalInputPanel } from "@/components/operations/OperationalInputPanel";
import { ApiError } from "@/lib/api/client";
import { getCompanyIntelligenceProfile, updateCompanyIntelligenceProfile } from "@/lib/api/company-profile";
import { listDepartments } from "@/lib/api/departments";
import {
  DEMO_COMPANY,
  DEMO_DEPARTMENTS,
} from "@/lib/demo-data";
import { translate, type Language } from "@/lib/i18n";
import type { CompanyIntelligenceProfile, Department } from "@/lib/types";

type ActiveWorkspace =
  | {
      kind: "ceo";
    }
  | {
      kind: "division";
      divisionKey: DivisionKey;
    }
  | {
      kind: "memory" | "reports" | "automations" | "settings";
    };

type DivisionKey = "dairtna" | "caesar" | "shared";

type BrainWorkspace =
  | {
      kind: "ceo";
      label: string;
      badge: string;
      description: string;
    }
  | {
      kind: "division";
      divisionKey: DivisionKey;
      label: string;
      badge: string;
      description: string;
    }
  | {
      kind: "memory" | "reports" | "automations" | "settings";
      label: string;
      badge: string;
      description: string;
    };

type Signal = {
  label: string;
  value: string;
  tone?: "good" | "warn" | "risk" | "neutral";
};

type DivisionConfig = {
  title: string;
  subtitle: string;
  scope: string;
  signals: Signal[];
  risks: string[];
  positives: string[];
  actions: string[];
  relatedFiles: string[];
};

const brainWorkspaces: BrainWorkspace[] = [
  {
    kind: "ceo",
    label: "CEO Brain",
    badge: "CEO",
    description: "Company-wide reasoning",
  },
  {
    kind: "division",
    divisionKey: "dairtna",
    label: "Dairtna Poultry",
    badge: "DP",
    description: "Poultry operations",
  },
  {
    kind: "division",
    divisionKey: "caesar",
    label: "Caesar Beverage",
    badge: "CB",
    description: "Beverage operations",
  },
  {
    kind: "division",
    divisionKey: "shared",
    label: "Shared Corporate",
    badge: "SC",
    description: "HR, finance, procurement",
  },
  {
    kind: "memory",
    label: "Company Memory",
    badge: "MEM",
    description: "Files, updates, decisions",
  },
  {
    kind: "reports",
    label: "Reports",
    badge: "RPT",
    description: "Briefings and summaries",
  },
  {
    kind: "automations",
    label: "Automations",
    badge: "AUTO",
    description: "Future triggers",
  },
  {
    kind: "settings",
    label: "Settings",
    badge: "SET",
    description: "Company context",
  },
];

const divisionConfigs: Record<"ceo" | DivisionKey | "memory" | "reports" | "automations", DivisionConfig> = {
  ceo: {
    title: "CEO Brain",
    subtitle:
      "Ask NAWA anything: operational analysis, executive reports, SOPs, PPT outlines, avatar briefings, and automation-ready actions.",
    scope: "Jannat Al-Firdaws",
    signals: [
      { label: "Dairtna Poultry", value: "Feed, halls, production, veterinary, sales", tone: "warn" },
      { label: "Caesar Beverage", value: "Production, warehouse, distribution, marketing", tone: "neutral" },
      { label: "Shared Corporate", value: "HR coverage, procurement, finance control", tone: "good" },
    ],
    risks: [
      "Production promises need warehouse and logistics confirmation before Sales commits.",
      "HR attendance and leave signals can quietly create execution risk.",
      "Procurement timing depends on finance approval and supplier readiness.",
    ],
    positives: [
      "Native operational inputs are available even before ERP integration.",
      "Decision context can already combine memory, files, events, and patterns.",
    ],
    actions: [
      "Ask for today's cross-division risk summary.",
      "Upload operating files or add manual updates before requesting reports.",
      "Generate a CEO briefing for Dairtna, Caesar, and Shared Corporate.",
    ],
    relatedFiles: ["Executive operating brief", "Company profile", "Department dependencies"],
  },
  dairtna: {
    title: "Dairtna Poultry",
    subtitle:
      "Poultry intelligence across halls, feed, egg production, veterinary, warehouse, sales/distribution, and finance signals.",
    scope: "Jannat Al-Firdaws / Dairtna Poultry",
    signals: [
      { label: "Halls overview", value: "Hall status, flock pressure, capacity", tone: "neutral" },
      { label: "Feed signals", value: "Feed withdrawal, silo balance, supplier risk", tone: "warn" },
      { label: "Egg production", value: "Output direction, yield movement, losses", tone: "risk" },
      { label: "Veterinary", value: "Mortality, medication, disease alerts", tone: "warn" },
      { label: "Sales/distribution", value: "Demand, delivery, route readiness", tone: "neutral" },
      { label: "Finance", value: "Feed cost, cash, procurement approvals", tone: "neutral" },
    ],
    risks: [
      "Feed shortage can become production drop and finance pressure in the same cycle.",
      "Hall health issues affect sales availability, logistics planning, and cash expectations.",
      "Production updates without veterinary context can hide root cause.",
    ],
    positives: [
      "Arabic natural updates can capture halls, quantities, feed, and production direction.",
      "Dairtna can run natively before ERP and still feed operational memory.",
    ],
    actions: [
      "Ask NAWA to explain today's hall/feed/production chain.",
      "Add a hall update with quantities and issue words.",
      "Generate a Dairtna poultry morning briefing.",
    ],
    relatedFiles: ["Poultry hall SOP", "Feed consumption sheet", "Veterinary notes"],
  },
  caesar: {
    title: "Caesar Beverage",
    subtitle:
      "Beverage intelligence across production, warehouse, sales/distribution, marketing, and finance signals.",
    scope: "Jannat Al-Firdaws / Caesar Beverage",
    signals: [
      { label: "Production", value: "Line output, downtime, batch quality", tone: "neutral" },
      { label: "Warehouse", value: "Stock accuracy, aging, release readiness", tone: "warn" },
      { label: "Sales/distribution", value: "Orders, route load, customer commitments", tone: "neutral" },
      { label: "Marketing", value: "Campaign demand, promo pressure", tone: "good" },
      { label: "Finance", value: "Margin, collections, promo cost", tone: "neutral" },
    ],
    risks: [
      "Campaign demand can outpace stock and route capacity.",
      "Warehouse aging and production timing affect discount and margin decisions.",
    ],
    positives: [
      "Marketing and Sales signals can be interpreted against warehouse readiness.",
      "Reports can connect campaign lift to operational capacity.",
    ],
    actions: [
      "Ask for Caesar production-to-distribution bottlenecks.",
      "Create a campaign readiness checklist.",
      "Generate a beverage sales and warehouse brief.",
    ],
    relatedFiles: ["Beverage production plan", "Warehouse stock report", "Campaign calendar"],
  },
  shared: {
    title: "Shared Corporate",
    subtitle:
      "Shared intelligence across HR, procurement, corporate finance, assets, governance, and executive follow-up.",
    scope: "Jannat Al-Firdaws / Shared Corporate Departments",
    signals: [
      { label: "HR", value: "Attendance, leave, shifts, performance notes", tone: "warn" },
      { label: "Procurement", value: "Supplier readiness, purchase approvals", tone: "neutral" },
      { label: "Corporate Finance", value: "Cash, budget, accounting signals", tone: "neutral" },
      { label: "Assets", value: "Equipment, maintenance, utilization", tone: "good" },
    ],
    risks: [
      "Attendance gaps can break plans that look healthy in production or logistics.",
      "Finance approval delays can block procurement and scaling.",
      "Asset downtime can appear as department underperformance unless linked.",
    ],
    positives: [
      "Shared functions can be analyzed as execution enablers, not back-office tables.",
      "HR signals are available to decision context and pattern detection.",
    ],
    actions: [
      "Ask for HR impact on today's execution risk.",
      "Create a procurement approval follow-up report.",
      "Draft a shared corporate weekly briefing.",
    ],
    relatedFiles: ["HR attendance summary", "Procurement approvals", "Asset register"],
  },
  memory: {
    title: "Company Memory",
    subtitle: "Operational memory from chats, files, manual updates, forms, future ERP inputs, and automations.",
    scope: "Company-wide memory",
    signals: [
      { label: "Raw inputs", value: "Stored before parsing", tone: "good" },
      { label: "Files", value: "Knowledge and operational evidence", tone: "neutral" },
      { label: "Events", value: "Operational signals for patterns", tone: "warn" },
    ],
    risks: ["Unreviewed files may lack extracted context until processed."],
    positives: ["No input is lost before classification."],
    actions: ["Upload files, add updates, then ask NAWA to summarize evidence."],
    relatedFiles: ["Uploaded files", "Decision memory", "Operational update stream"],
  },
  reports: {
    title: "Reports",
    subtitle: "Ask NAWA to generate executive reports, SOPs, PPT outlines, operating briefs, and avatar briefing scripts.",
    scope: "Generated intelligence",
    signals: [
      { label: "CEO brief", value: "Risks, positives, actions", tone: "good" },
      { label: "SOP", value: "Workflow-ready procedures", tone: "neutral" },
      { label: "PPT", value: "Slide narrative and sections", tone: "neutral" },
    ],
    risks: ["Reports are strongest after files and daily updates are captured."],
    positives: ["Decision context carries memory, patterns, and organization dependencies."],
    actions: ["Ask: create a CEO report for Dairtna and Caesar today."],
    relatedFiles: ["Board narrative", "Executive report", "SOP drafts"],
  },
  automations: {
    title: "Automations",
    subtitle: "Future workspace for n8n, ERP triggers, alerts, report schedules, and action routing.",
    scope: "Automation-ready intelligence",
    signals: [
      { label: "Triggers", value: "Planned for risks and recurring patterns", tone: "warn" },
      { label: "n8n", value: "Future automation input/output", tone: "neutral" },
      { label: "Alerts", value: "Event-driven follow-up", tone: "neutral" },
    ],
    risks: ["Automation execution is intentionally planned, not forced into this MVP."],
    positives: ["Current raw-input/event architecture is ready for automation triggers."],
    actions: ["Ask NAWA to design an automation flow before implementation."],
    relatedFiles: ["Automation backlog", "Integration providers", "Alert rules"],
  },
};

const emptyCompanyProfile: CompanyIntelligenceProfile = {
  company_name: "",
  industry: "",
  business_type: "B2B",
  country_market: "",
  company_size: "",
  departments_enabled: [],
  primary_goals: "",
  current_operational_challenges: "",
  growth_priorities: "",
  preferred_response_language: "en",
  is_active: false,
};

export function WorkspaceShell() {
  const { me, token, logout } = useAuth();
  const { direction, language, t } = useLanguage();
  const permissions = me?.role.permissions ?? [];
  const [departments, setDepartments] = useState<Department[]>([]);
  const [departmentStatus, setDepartmentStatus] = useState<"idle" | "loading" | "ready" | "blocked" | "error">(
    "idle",
  );
  const [departmentError, setDepartmentError] = useState<string | null>(null);
  const [activeWorkspace, setActiveWorkspace] = useState<ActiveWorkspace>({ kind: "ceo" });
  const [companyProfile, setCompanyProfile] = useState<CompanyIntelligenceProfile>(emptyCompanyProfile);
  const [profileStatus, setProfileStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [awarenessRefreshKey, setAwarenessRefreshKey] = useState(0);

  const canReadDepartments = hasPermission(permissions, "departments.read");
  const canReadFiles = hasPermission(permissions, "files.read");
  const canSubmitOperationalForms = hasPermission(permissions, "operational.forms.submit");
  const canUseCeoWorkspace = hasPermission(permissions, "workspace.ceo");

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

  useEffect(() => {
    if (!token) {
      setCompanyProfile(emptyCompanyProfile);
      setProfileStatus("idle");
      return;
    }

    let isMounted = true;
    setProfileStatus("loading");

    getCompanyIntelligenceProfile(token)
      .then((profile) => {
        if (!isMounted) {
          return;
        }
        setCompanyProfile(profile);
        setProfileStatus("ready");
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setProfileStatus("error");
      });

    return () => {
      isMounted = false;
    };
  }, [token]);

  const displayDepartments = departments.length > 0 ? departments : DEMO_DEPARTMENTS;
  const activeConfig = getWorkspaceConfig(activeWorkspace);
  const activeDepartment = useMemo(
    () => resolveWorkspaceDepartment(activeWorkspace, displayDepartments, permissions),
    [activeWorkspace, displayDepartments, permissions],
  );
  const naturalCaptureDepartment = useMemo(
    () =>
      activeDepartment && departments.some((department) => department.id === activeDepartment.id)
        ? activeDepartment
        : null,
    [activeDepartment, departments],
  );
  const activeWorkspaceKey = getWorkspaceKey(activeWorkspace, activeDepartment);
  const chatTitle = localizeWorkspaceText(activeConfig.title, language);
  const canUseActiveDepartment = activeDepartment ? canUseAgent(permissions, activeDepartment.department_type) : true;
  const canChatInWorkspace = activeWorkspace.kind === "ceo" ? canUseCeoWorkspace : true;
  const canSubmitInWorkspace = Boolean(
    token &&
      canSubmitOperationalForms &&
      (canUseCeoWorkspace || activeWorkspace.kind === "division" || canUseActiveDepartment),
  );

  return (
    <main className="min-h-screen text-ink" dir={direction}>
      <header className="border-b border-white/10 bg-executive text-white">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md border border-white/15 bg-white/10 text-sm font-semibold text-white">
              N
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide text-white">{t("workspaceShell.companyName")}</div>
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

      <div className="mx-auto grid max-w-[1600px] gap-4 px-4 py-4 sm:px-6 xl:grid-cols-[280px_minmax(0,1fr)_360px]">
        <BrainSidebar
          activeWorkspace={activeWorkspace}
          companyProfileActive={companyProfile.is_active}
          departmentStatus={departmentStatus}
          departmentError={departmentError}
          permissionsCount={permissions.length}
          roleName={me?.role.name || DEMO_COMPANY.role}
          canUseCeoWorkspace={canUseCeoWorkspace}
          onSelect={setActiveWorkspace}
        />

        <section className="min-w-0 space-y-4">
          <CompanyBrainHeader
            config={activeConfig}
            companyProfileActive={companyProfile.is_active}
            canChatInWorkspace={canChatInWorkspace}
          />

          {activeWorkspace.kind === "settings" ? (
            <CompanyProfilePanel
              token={token}
              profile={companyProfile}
              profileStatus={profileStatus}
              departments={displayDepartments}
              onSaved={setCompanyProfile}
            />
          ) : (
            <>
              {token && me ? (
                <>
                  <ChatPanel
                    token={token}
                    companyId={me.company.id}
                    workspaceKey={activeWorkspaceKey}
                    title={chatTitle}
                    department={activeDepartment}
                  />
                </>
              ) : null}

              {activeWorkspace.kind === "division" && activeWorkspace.divisionKey === "dairtna" ? (
                <>
                  <NaturalOperationalCapturePanel
                    token={token || ""}
                    departments={departments}
                    defaultDepartment={naturalCaptureDepartment}
                    canSubmit={canSubmitInWorkspace}
                    onCaptured={() => setAwarenessRefreshKey((current) => current + 1)}
                  />
                  <OperationalAwarenessPanel token={token || ""} refreshKey={awarenessRefreshKey} />
                  <ManualOperationalEventPanel
                    token={token || ""}
                    departments={displayDepartments}
                    defaultDepartment={activeDepartment}
                    canSubmit={canSubmitInWorkspace}
                  />
                </>
              ) : null}

              <OperationalInputPanel
                token={token || ""}
                department={activeDepartment}
                departments={displayDepartments}
                canSubmit={canSubmitInWorkspace}
                canUpload={Boolean(token && canReadFiles)}
                canAssignDepartment={canUseCeoWorkspace}
              />
            </>
          )}
        </section>

        <aside className="space-y-4 xl:sticky xl:top-4 xl:h-fit">
          <IntelligencePanel
            config={activeConfig}
            companyProfileActive={companyProfile.is_active}
            activeWorkspace={activeWorkspace}
          />
          {token && canReadFiles ? (
            <FilesPanel
              token={token}
              departments={displayDepartments}
              activeDepartmentId={canUseCeoWorkspace ? null : activeDepartment?.id ?? null}
            />
          ) : null}
        </aside>
      </div>
    </main>
  );
}

function BrainSidebar({
  activeWorkspace,
  companyProfileActive,
  departmentStatus,
  departmentError,
  permissionsCount,
  roleName,
  canUseCeoWorkspace,
  onSelect,
}: {
  activeWorkspace: ActiveWorkspace;
  companyProfileActive: boolean;
  departmentStatus: "idle" | "loading" | "ready" | "blocked" | "error";
  departmentError: string | null;
  permissionsCount: number;
  roleName: string;
  canUseCeoWorkspace: boolean;
  onSelect: (workspace: ActiveWorkspace) => void;
}) {
  const { language, t } = useLanguage();

  return (
    <aside className="command-panel h-fit p-3 xl:sticky xl:top-4">
      <div className="px-2 pb-3">
        <div className="text-xs font-semibold uppercase text-white/55">{t("workspaceShell.company")}</div>
        <div className="mt-1 text-base font-semibold text-white">{t("workspaceShell.companyName")}</div>
        <div className="mt-1 text-xs leading-5 text-white/55">{t("workspaceShell.companyBrainOperationalIntelligence")}</div>
      </div>

      <nav className="space-y-1">
        {brainWorkspaces.map((workspace) => {
          const workspaceKey = workspace.kind === "division" ? workspace.divisionKey : workspace.kind;
          const active =
            activeWorkspace.kind === workspace.kind &&
            (workspace.kind !== "division" ||
              (activeWorkspace.kind === "division" && activeWorkspace.divisionKey === workspace.divisionKey));
          const disabled = workspace.kind === "ceo" && !canUseCeoWorkspace;
          return (
            <SidebarItem
              key={workspaceKey}
              label={localizeWorkspaceText(workspace.label, language)}
              description={localizeWorkspaceText(workspace.description, language)}
              badge={workspace.badge}
              active={active}
              disabled={disabled}
              lockLabel={t("locked")}
              onClick={() => {
                if (workspace.kind === "division") {
                  onSelect({ kind: "division", divisionKey: workspace.divisionKey });
                } else {
                  onSelect({ kind: workspace.kind });
                }
              }}
            />
          );
        })}
      </nav>

      <div className="mt-4 space-y-3 border-t border-white/10 px-2 pt-3">
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

        <div>
          <div className="text-xs font-semibold uppercase text-white/60">{t("role")}</div>
          <div className="mt-1 text-sm font-medium text-white">{localizeWorkspaceText(roleName, language)}</div>
          <div className="mt-1 text-xs text-white/60">
            {permissionsCount} {t("permissionsAvailable")}
          </div>
        </div>
        <div className="rounded-md border border-white/10 bg-white/5 p-2.5 text-xs leading-5 text-white/60">
          <span className={companyProfileActive ? "text-gold" : "text-white/60"}>
            {companyProfileActive ? t("companyContextActive") : t("companyContextInactive")}
          </span>
          <span className="block">{t("workspaceShell.erpOneSource")}</span>
        </div>
      </div>
    </aside>
  );
}

function CompanyBrainHeader({
  config,
  companyProfileActive,
  canChatInWorkspace,
}: {
  config: DivisionConfig;
  companyProfileActive: boolean;
  canChatInWorkspace: boolean;
}) {
  const { language, t } = useLanguage();

  return (
    <section className="command-panel p-4">
      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
        <div>
          <div className="text-xs font-semibold uppercase text-white/60">{t("liveAiWorkforce")}</div>
          <h1 className="mt-1 text-2xl font-semibold text-white">{localizeWorkspaceText(config.title, language)}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-white/70">
            {localizeWorkspaceText(config.subtitle, language)}
          </p>
        </div>
        <div className="grid gap-2 text-xs text-white/70 sm:grid-cols-2 lg:min-w-80">
          <div className="rounded-md border border-white/10 bg-white/10 px-3 py-2">
            <span className="block text-white/45">{t("scope")}</span>
            <span className="mt-1 block font-medium text-white">{localizeWorkspaceText(config.scope, language)}</span>
          </div>
          <div className="rounded-md border border-white/10 bg-white/10 px-3 py-2">
            <span className="block text-white/45">{t("workspaceShell.context")}</span>
            <span className="mt-1 block font-medium text-white">
              {companyProfileActive ? t("companyContextActive") : t("companyContextInactive")}
            </span>
          </div>
          {!canChatInWorkspace ? (
            <div className="rounded-md border border-amber-300/30 bg-amber-300/10 px-3 py-2 sm:col-span-2">
              {t("workspaceUnavailable")}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function IntelligencePanel({
  config,
  companyProfileActive,
  activeWorkspace,
}: {
  config: DivisionConfig;
  companyProfileActive: boolean;
  activeWorkspace: ActiveWorkspace;
}) {
  const { language, t } = useLanguage();

  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-line bg-white px-4 py-3">
        <div className="executive-label">{t("workspaceShell.liveCompanyIntelligence")}</div>
        <h2 className="mt-1 text-base font-semibold text-ink">{localizeWorkspaceText(config.title, language)}</h2>
      </div>
      <div className="space-y-4 bg-white p-4">
        <IntelligenceSection title="Active division">
          <div className="rounded-md border border-line bg-surface px-3 py-2 text-sm text-ink">
            {localizeWorkspaceText(config.scope, language)}
          </div>
        </IntelligenceSection>

        <IntelligenceSection title="Live signals">
          <div className="space-y-2">
            {config.signals.map((signal) => (
              <SignalRow key={signal.label} signal={signal} />
            ))}
          </div>
        </IntelligenceSection>

        <IntelligenceSection title="Detected risks">
          <InsightList items={config.risks} tone="risk" />
        </IntelligenceSection>

        <IntelligenceSection title="Positive signals">
          <InsightList items={config.positives} tone="good" />
        </IntelligenceSection>

        <IntelligenceSection title="Suggested actions">
          <InsightList items={config.actions} tone="neutral" />
        </IntelligenceSection>

        <IntelligenceSection title="Related files">
          <div className="flex flex-wrap gap-2">
            {config.relatedFiles.map((file) => (
              <span key={file} className="rounded-md border border-line bg-surface px-2 py-1 text-xs text-muted">
                {localizeWorkspaceText(file, language)}
              </span>
            ))}
          </div>
        </IntelligenceSection>

        <div className="rounded-md border border-line bg-surface p-3 text-xs leading-5 text-muted">
          <span className="font-semibold text-ink">{t("companyContextActive")}: </span>
          {companyProfileActive ? t("companyContextActive") : t("companyContextInactive")}
          <span className="mt-1 block">
            {t("workspaceShell.modeLabel")}:{" "}
            {activeWorkspace.kind === "settings" ? t("workspaceShell.modeSettings") : t("workspaceShell.modeCompanyBrain")}
          </span>
        </div>
      </div>
    </section>
  );
}

function IntelligenceSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-2 text-xs font-semibold uppercase text-muted">{title}</div>
      {children}
    </div>
  );
}

function SignalRow({ signal }: { signal: Signal }) {
  const { language } = useLanguage();
  const toneClass =
    signal.tone === "good"
      ? "border-emerald-200 bg-emerald-50"
      : signal.tone === "risk"
        ? "border-red-200 bg-red-50"
        : signal.tone === "warn"
          ? "border-amber-200 bg-amber-50"
          : "border-line bg-surface";

  return (
    <div className={`rounded-md border px-3 py-2 ${toneClass}`}>
      <div className="text-sm font-medium text-ink">{localizeWorkspaceText(signal.label, language)}</div>
      <div className="mt-0.5 text-xs leading-5 text-muted">{localizeWorkspaceText(signal.value, language)}</div>
    </div>
  );
}

function InsightList({ items, tone }: { items: string[]; tone: "good" | "risk" | "neutral" }) {
  const { language } = useLanguage();
  const markerClass = tone === "good" ? "bg-emerald-500" : tone === "risk" ? "bg-red-500" : "bg-accent";

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div key={item} className="flex gap-2 text-sm leading-6 text-muted">
          <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${markerClass}`} />
          <span>{localizeWorkspaceText(item, language)}</span>
        </div>
      ))}
    </div>
  );
}

function CompanyProfilePanel({
  token,
  profile,
  profileStatus,
  departments,
  onSaved,
}: {
  token: string | null;
  profile: CompanyIntelligenceProfile;
  profileStatus: "idle" | "loading" | "ready" | "error";
  departments: Department[];
  onSaved: (profile: CompanyIntelligenceProfile) => void;
}) {
  const { language, t } = useLanguage();
  const [draft, setDraft] = useState<CompanyIntelligenceProfile>(profile);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  useEffect(() => {
    setDraft(profile);
  }, [profile]);

  async function handleSave() {
    if (!token || saveStatus === "saving") {
      return;
    }

    setSaveStatus("saving");
    try {
      const saved = await updateCompanyIntelligenceProfile(token, draft);
      onSaved(saved);
      setSaveStatus("saved");
    } catch {
      setSaveStatus("error");
    }
  }

  function updateField<K extends keyof CompanyIntelligenceProfile>(key: K, value: CompanyIntelligenceProfile[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  function toggleDepartment(name: string) {
    const current = new Set(draft.departments_enabled);
    if (current.has(name)) {
      current.delete(name);
    } else {
      current.add(name);
    }
    updateField("departments_enabled", Array.from(current));
  }

  return (
    <section className="panel p-5">
      <div className="flex flex-col justify-between gap-3 border-b border-line pb-4 md:flex-row md:items-start">
        <div>
          <div className="executive-label">{t("settings")}</div>
          <h2 className="mt-1 text-lg font-semibold text-ink">{t("companyIntelligenceProfile")}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">{t("companyProfileDescription")}</p>
        </div>
        <span
          className={`rounded-md border px-3 py-2 text-xs font-medium ${
            draft.is_active
              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
              : "border-line bg-surface text-muted"
          }`}
        >
          {draft.is_active ? t("companyContextActive") : t("companyContextInactive")}
        </span>
      </div>

      {profileStatus === "loading" ? (
        <div className="mt-4 text-sm text-muted">{t("loadingCompanyProfile")}</div>
      ) : null}

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <ProfileField
          label={t("profileCompanyName")}
          value={draft.company_name}
          onChange={(value) => updateField("company_name", value)}
        />
        <ProfileField label={t("profileIndustry")} value={draft.industry} onChange={(value) => updateField("industry", value)} />
        <label className="space-y-1.5">
          <span className="text-xs font-semibold uppercase text-muted">{t("profileBusinessType")}</span>
          <select
            className="input"
            value={draft.business_type}
            onChange={(event) => updateField("business_type", event.target.value)}
          >
            <option value="B2B">B2B</option>
            <option value="B2C">B2C</option>
            <option value="Hybrid">Hybrid</option>
          </select>
        </label>
        <ProfileField
          label={t("profileCountryMarket")}
          value={draft.country_market}
          onChange={(value) => updateField("country_market", value)}
        />
        <ProfileField
          label={t("profileCompanySize")}
          value={draft.company_size}
          onChange={(value) => updateField("company_size", value)}
        />
        <label className="space-y-1.5">
          <span className="text-xs font-semibold uppercase text-muted">{t("profilePreferredLanguage")}</span>
          <select
            className="input"
            value={draft.preferred_response_language}
            onChange={(event) => updateField("preferred_response_language", event.target.value as "en" | "ar")}
          >
            <option value="en">English</option>
            <option value="ar">العربية</option>
          </select>
        </label>
      </div>

      <div className="mt-5">
        <div className="text-xs font-semibold uppercase text-muted">{t("profileDepartmentsEnabled")}</div>
        <div className="mt-2 flex flex-wrap gap-2">
          {departments.map((department) => {
            const selected = draft.departments_enabled.includes(department.name);
            return (
              <button
                key={department.id}
                className={`rounded-md border px-3 py-2 text-sm transition ${
                  selected ? "border-accent/30 bg-accent/10 text-accent" : "border-line bg-white text-muted hover:text-ink"
                }`}
                type="button"
                onClick={() => toggleDepartment(department.name)}
              >
                {localizeDepartmentName(department.name, language)}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-5 grid gap-4">
        <ProfileTextarea
          label={t("profilePrimaryGoals")}
          value={draft.primary_goals}
          onChange={(value) => updateField("primary_goals", value)}
        />
        <ProfileTextarea
          label={t("profileOperationalChallenges")}
          value={draft.current_operational_challenges}
          onChange={(value) => updateField("current_operational_challenges", value)}
        />
        <ProfileTextarea
          label={t("profileGrowthPriorities")}
          value={draft.growth_priorities}
          onChange={(value) => updateField("growth_priorities", value)}
        />
      </div>

      <div className="mt-5 flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="text-sm text-muted">
          {saveStatus === "saved"
            ? t("profileSaved")
            : saveStatus === "error" || profileStatus === "error"
              ? t("profileSaveError")
              : t("profileSaveHint")}
        </div>
        <button className="button-primary sm:w-36" type="button" onClick={handleSave} disabled={!token || saveStatus === "saving"}>
          {saveStatus === "saving" ? t("saving") : t("saveProfile")}
        </button>
      </div>
    </section>
  );
}

function ProfileField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="space-y-1.5">
      <span className="text-xs font-semibold uppercase text-muted">{label}</span>
      <input className="input" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function ProfileTextarea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="space-y-1.5">
      <span className="text-xs font-semibold uppercase text-muted">{label}</span>
      <textarea className="input min-h-24 resize-none leading-6" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
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

function getWorkspaceConfig(workspace: ActiveWorkspace): DivisionConfig {
  if (workspace.kind === "division") {
    return divisionConfigs[workspace.divisionKey];
  }
  if (workspace.kind === "settings") {
    return {
      ...divisionConfigs.memory,
      title: "Settings",
      subtitle: "Company context and organizational intelligence controls for NAWA.",
      scope: "Jannat Al-Firdaws settings",
    };
  }
  return divisionConfigs[workspace.kind];
}

function getWorkspaceKey(workspace: ActiveWorkspace, department: Department | null): string {
  if (workspace.kind === "division") {
    return `division-${workspace.divisionKey}-${department?.id ?? "company"}`;
  }
  return workspace.kind;
}

function resolveWorkspaceDepartment(
  workspace: ActiveWorkspace,
  departments: Department[],
  permissions: string[],
): Department | null {
  if (workspace.kind !== "division") {
    return null;
  }
  const preferredTypes: Record<DivisionKey, string[]> = {
    dairtna: ["production_ai", "warehouse_ai", "operations_ai", "finance_ai"],
    caesar: ["operations_ai", "sales_ai", "marketing_ai", "warehouse_ai", "finance_ai"],
    shared: ["hr_ai", "finance_ai", "operations_ai"],
  };
  return (
    preferredTypes[workspace.divisionKey]
      .map((departmentType) =>
        departments.find(
          (department) =>
            department.department_type === departmentType &&
            department.ai_agent_enabled &&
            canUseAgent(permissions, department.department_type),
        ),
      )
      .find((department): department is Department => Boolean(department)) ?? null
  );
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

function localizeWorkspaceText(value: string, language: Language): string {
  if (language === "en") {
    return value;
  }

  const nawaTranslations: Record<string, string> = {
    "CEO Brain": "workspaceShell.workspaces.ceo.label",
    "Company-wide reasoning": "workspaceShell.workspaces.ceo.description",
    "Dairtna Poultry": "workspaceShell.workspaces.dairtna.label",
    "Poultry operations": "workspaceShell.workspaces.dairtna.description",
    "Poultry intelligence across halls, feed, egg production, veterinary, warehouse, sales/distribution, and finance signals.":
      "workspaceShell.workspaces.dairtna.subtitle",
    "Jannat Al-Firdaws / Dairtna Poultry": "workspaceShell.workspaces.dairtna.scope",
    "Caesar Beverage": "workspaceShell.workspaces.caesar.label",
    "Beverage operations": "workspaceShell.workspaces.caesar.description",
    "Shared Corporate": "workspaceShell.workspaces.shared.label",
    "HR, finance, procurement": "workspaceShell.workspaces.shared.description",
    "Company Memory": "workspaceShell.workspaces.memory.label",
    "Files, updates, decisions": "workspaceShell.workspaces.memory.description",
    Reports: "workspaceShell.workspaces.reports.label",
    "Briefings and summaries": "workspaceShell.workspaces.reports.description",
    Automations: "workspaceShell.workspaces.automations.label",
    "Future triggers": "workspaceShell.workspaces.automations.description",
    Settings: "workspaceShell.workspaces.settings.label",
    "Company context": "workspaceShell.workspaces.settings.description",
    "Halls overview": "workspaceShell.dairtnaSignals.hallsOverview",
    "Hall status, flock pressure, capacity": "workspaceShell.dairtnaSignals.hallsOverviewValue",
    "Feed signals": "workspaceShell.dairtnaSignals.feedSignals",
    "Feed withdrawal, silo balance, supplier risk": "workspaceShell.dairtnaSignals.feedSignalsValue",
    "Egg production": "workspaceShell.dairtnaSignals.eggProduction",
    "Output direction, yield movement, losses": "workspaceShell.dairtnaSignals.eggProductionValue",
    Veterinary: "workspaceShell.dairtnaSignals.veterinary",
    "Mortality, medication, disease alerts": "workspaceShell.dairtnaSignals.veterinaryValue",
    "Sales/distribution": "workspaceShell.dairtnaSignals.salesDistribution",
    "Demand, delivery, route readiness": "workspaceShell.dairtnaSignals.salesDistributionValue",
    Finance: "workspaceShell.dairtnaSignals.finance",
    "Feed cost, cash, procurement approvals": "workspaceShell.dairtnaSignals.financeValue",
    "Feed shortage can become production drop and finance pressure in the same cycle.":
      "workspaceShell.dairtnaInsights.riskFeed",
    "Hall health issues affect sales availability, logistics planning, and cash expectations.":
      "workspaceShell.dairtnaInsights.riskHealth",
    "Production updates without veterinary context can hide root cause.":
      "workspaceShell.dairtnaInsights.riskProduction",
    "Arabic natural updates can capture halls, quantities, feed, and production direction.":
      "workspaceShell.dairtnaInsights.positiveArabic",
    "Dairtna can run natively before ERP and still feed operational memory.":
      "workspaceShell.dairtnaInsights.positiveNative",
    "Ask NAWA to explain today's hall/feed/production chain.":
      "workspaceShell.dairtnaInsights.actionChain",
    "Add a hall update with quantities and issue words.":
      "workspaceShell.dairtnaInsights.actionUpdate",
    "Generate a Dairtna poultry morning briefing.":
      "workspaceShell.dairtnaInsights.actionBrief",
    "Poultry hall SOP": "workspaceShell.dairtnaInsights.fileSop",
    "Feed consumption sheet": "workspaceShell.dairtnaInsights.fileFeed",
    "Veterinary notes": "workspaceShell.dairtnaInsights.fileVet",
  };
  const nawaKey = nawaTranslations[value];
  if (nawaKey) {
    return translate(language, nawaKey);
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
    "Company Brain workspace for organizational intelligence, live operational awareness, cross-department priorities, and enterprise decisions.":
      "مساحة Company Brain للاستحبارات التنظيمية والوعي التشغيلي الحي والأولويات بين الأقسام.",
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
