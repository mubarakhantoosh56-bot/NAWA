"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { FilesPanel } from "@/components/files/FilesPanel";
import { LanguageToggle } from "@/components/i18n/LanguageToggle";
import { useLanguage } from "@/components/i18n/LanguageProvider";
import { CompanyInputsPanel } from "@/components/operations/CompanyInputsPanel";
import { ManualOperationalEventPanel } from "@/components/operations/ManualOperationalEventPanel";
import { NaturalOperationalCapturePanel } from "@/components/operations/NaturalOperationalCapturePanel";
import { OperationalAwarenessPanel } from "@/components/operations/OperationalAwarenessPanel";
import { ApiError } from "@/lib/api/client";
import { getCompanyIntelligenceProfile, updateCompanyIntelligenceProfile } from "@/lib/api/company-profile";
import { listDepartments } from "@/lib/api/departments";
import {
  DEMO_COMPANY,
  DEMO_DEPARTMENTS,
} from "@/lib/demo-data";
import { isDemoModeEnabled } from "@/lib/demo-mode";
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
      kind: "inputs" | "memory" | "reports" | "automations" | "settings";
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
      kind: "inputs" | "memory" | "reports" | "automations" | "settings";
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
    kind: "inputs",
    label: "Company Inputs",
    badge: "IN",
    description: "Excel, PDF, text updates",
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

const divisionConfigs: Record<"ceo" | DivisionKey | "inputs" | "memory" | "reports" | "automations", DivisionConfig> = {
  ceo: {
    title: "Executive Command Center",
    subtitle:
      "Organizational intelligence for Jannat Al-Firdaws — Dairtna Poultry, Caesar Beverage, and Shared Corporate. Cross-division decisions, operational signals, and AI briefings.",
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
  inputs: {
    title: "Company Inputs",
    subtitle:
      "One entry point for Excel, PDF, and operational text updates. NAWA classifies each input and routes it through the existing runtime.",
    scope: "Company-wide intake",
    signals: [
      { label: "Excel", value: "Operational reports and daily sheets", tone: "good" },
      { label: "PDF", value: "Documents and policies", tone: "neutral" },
      { label: "Text", value: "Operational updates from teams", tone: "warn" },
    ],
    risks: ["Low-confidence inputs wait for clarification instead of being guessed."],
    positives: ["Users submit company information without choosing internal systems."],
    actions: ["Upload a report or add today's operational update."],
    relatedFiles: ["Daily report", "Policy document", "Field update"],
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

// Only "ceo"/"dairtna"/"caesar"/"shared" carry hardcoded business-intelligence
// content (signals/risks/positives/actions/relatedFiles describing simulated
// company operations). "inputs"/"memory"/"reports"/"automations" describe the
// feature itself, not fabricated business data, and are left untouched.
const BUSINESS_INTELLIGENCE_KEYS: Array<keyof typeof divisionConfigs> = [
  "ceo",
  "dairtna",
  "caesar",
  "shared",
];

// Real pilot mode: never present demo identity (company name, email, role) as
// if it belonged to the authenticated user. In the current app, WorkspaceShell
// only ever renders once RequireAuth has confirmed a real authenticated `me`,
// so this fallback is defensive-only -- but it must not fabricate identity if
// that guarantee is ever weakened.
function demoIdentityFallback(demoValue: string): string {
  return isDemoModeEnabled() ? demoValue : "";
}

function getDivisionIntelligence(key: keyof typeof divisionConfigs): DivisionConfig {
  const base = divisionConfigs[key];
  if (isDemoModeEnabled() || !BUSINESS_INTELLIGENCE_KEYS.includes(key)) {
    return base;
  }
  // Real pilot mode: never present hardcoded signals/risks/positives/actions
  // as if they were live intelligence. Title/subtitle/scope are navigational
  // labels, not simulated data, and are preserved.
  return { ...base, signals: [], risks: [], positives: [], actions: [], relatedFiles: [] };
}

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
  const [activeWorkspace, setActiveWorkspace] = useState<ActiveWorkspace>({ kind: "inputs" });
  const [companyProfile, setCompanyProfile] = useState<CompanyIntelligenceProfile>(emptyCompanyProfile);
  const [profileStatus, setProfileStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [awarenessRefreshKey, setAwarenessRefreshKey] = useState(0);

  const canReadDepartments = hasPermission(permissions, "departments.read");
  const canReadFiles = hasPermission(permissions, "files.read");
  const canUploadFiles = hasPermission(permissions, "files.upload");
  const canSubmitOperationalForms = hasPermission(permissions, "operational.forms.submit");
  const canUseCeoWorkspace = hasPermission(permissions, "workspace.ceo");
  // M8 Slice 3B-2: existing, already-defined backend permission (reused
  // as-is, no new RBAC concept) - gates the Record Decision action inside
  // ChatPanel. The backend's own 403 remains authoritative regardless;
  // this only avoids showing an action that would predictably fail.
  const canRecordDecisions = hasPermission(permissions, "memory.write");

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

  const displayDepartments =
    departments.length === 0 && isDemoModeEnabled() ? DEMO_DEPARTMENTS : departments;
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
              <div className="text-sm font-medium">{me?.company.name || demoIdentityFallback(DEMO_COMPANY.name)}</div>
              <div className="text-xs text-white/60">{me?.user.email || demoIdentityFallback(DEMO_COMPANY.email)}</div>
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
          roleName={me?.role.name || demoIdentityFallback(DEMO_COMPANY.role)}
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
          ) : activeWorkspace.kind === "division" ? (
            <DivisionCommandCenter
              token={token}
              companyId={me?.company.id}
              divisionKey={activeWorkspace.divisionKey}
              activeDepartment={activeDepartment}
              departments={departments}
              displayDepartments={displayDepartments}
              naturalCaptureDepartment={naturalCaptureDepartment}
              canSubmit={canSubmitInWorkspace}
              canUpload={Boolean(token && canUploadFiles)}
              canUseCeoWorkspace={canUseCeoWorkspace}
              canRecordDecisions={canRecordDecisions}
              workspaceKey={activeWorkspaceKey}
              chatTitle={chatTitle}
              awarenessRefreshKey={awarenessRefreshKey}
              onCaptured={() => setAwarenessRefreshKey((current) => current + 1)}
            />
          ) : activeWorkspace.kind === "ceo" ? (
            <ExecutiveCommandCenter
              token={token}
              companyId={me?.company.id}
              workspaceKey={activeWorkspaceKey}
              chatTitle={chatTitle}
              activeDepartment={activeDepartment}
              displayDepartments={displayDepartments}
              canSubmit={canSubmitInWorkspace}
              canUpload={Boolean(token && canUploadFiles)}
              canUseCeoWorkspace={canUseCeoWorkspace}
              canRecordDecisions={canRecordDecisions}
              awarenessRefreshKey={awarenessRefreshKey}
              companyProfileActive={companyProfile.is_active}
              onNavigateDivision={(divisionKey) => setActiveWorkspace({ kind: "division", divisionKey })}
            />
          ) : activeWorkspace.kind === "inputs" ? (
            <CompanyInputsPanel
              token={token || ""}
              department={activeDepartment}
              departments={displayDepartments}
              canSubmit={canSubmitInWorkspace}
              canUpload={Boolean(token && canUploadFiles)}
              canAssignDepartment={canUseCeoWorkspace}
              onCaptured={() => setAwarenessRefreshKey((current) => current + 1)}
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
                    canRecordDecisions={canRecordDecisions}
                  />
                </>
              ) : null}
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
          <div className="text-xs font-semibold uppercase text-white/60">{t("enterpriseIntelligence")}</div>
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

type CeoSection = "overview" | "divisions" | "events" | "risks" | "files" | "briefings" | "memory";

function ExecutiveCommandCenter({
  token,
  companyId,
  workspaceKey,
  chatTitle,
  activeDepartment,
  displayDepartments,
  canSubmit,
  canUpload,
  canUseCeoWorkspace,
  canRecordDecisions,
  awarenessRefreshKey,
  companyProfileActive,
  onNavigateDivision,
}: {
  token: string | null;
  companyId: string | undefined;
  workspaceKey: string;
  chatTitle: string;
  activeDepartment: Department | null;
  displayDepartments: Department[];
  canSubmit: boolean;
  canUpload: boolean;
  canUseCeoWorkspace: boolean;
  canRecordDecisions: boolean;
  awarenessRefreshKey: number;
  companyProfileActive: boolean;
  onNavigateDivision: (key: DivisionKey) => void;
}) {
  const [activeSection, setActiveSection] = useState<CeoSection>("overview");
  const { t } = useLanguage();

  const sections: { key: CeoSection; label: string }[] = [
    { key: "overview", label: t("workspaceShell.ceoCenter.tabOverview") },
    { key: "divisions", label: t("workspaceShell.ceoCenter.tabDivisions") },
    { key: "events", label: t("workspaceShell.ceoCenter.tabEvents") },
    { key: "risks", label: t("workspaceShell.ceoCenter.tabRisks") },
    { key: "files", label: t("workspaceShell.ceoCenter.tabFiles") },
    { key: "briefings", label: t("workspaceShell.ceoCenter.tabBriefings") },
    { key: "memory", label: t("workspaceShell.ceoCenter.tabMemory") },
  ];

  return (
    <section className="panel overflow-hidden">
      <div className="flex overflow-x-auto border-b border-line bg-white">
        {sections.map((section) => (
          <button
            key={section.key}
            type="button"
            onClick={() => setActiveSection(section.key)}
            className={`whitespace-nowrap px-4 py-3 text-sm font-medium transition ${
              activeSection === section.key
                ? "border-b-2 border-accent text-accent"
                : "text-muted hover:text-ink"
            }`}
          >
            {section.label}
          </button>
        ))}
      </div>

      <div className="p-4">
        {activeSection === "overview" && (
          <ExecutiveOverviewSection
            companyProfileActive={companyProfileActive}
            onNavigateDivision={onNavigateDivision}
          />
        )}

        {activeSection === "divisions" && (
          <ExecutiveDivisionsSection onNavigateDivision={onNavigateDivision} />
        )}

        {activeSection === "events" && (
          <OperationalAwarenessPanel token={token || ""} refreshKey={awarenessRefreshKey} />
        )}

        {activeSection === "risks" && <ExecutiveRisksSection />}

        {activeSection === "files" && (
          <CompanyInputsPanel
            token={token || ""}
            department={activeDepartment}
            departments={displayDepartments}
            canSubmit={canSubmit}
            canUpload={canUpload}
            canAssignDepartment={canUseCeoWorkspace}
            onCaptured={() => undefined}
          />
        )}

        {activeSection === "briefings" &&
          (token && companyId ? (
            <ChatPanel
              token={token}
              companyId={companyId}
              workspaceKey={workspaceKey}
              title={chatTitle}
              department={activeDepartment}
              canRecordDecisions={canRecordDecisions}
            />
          ) : null)}

        {activeSection === "memory" && (
          <ExecutiveMemorySection companyProfileActive={companyProfileActive} />
        )}
      </div>
    </section>
  );
}

function ExecutiveOverviewSection({
  companyProfileActive,
  onNavigateDivision,
}: {
  companyProfileActive: boolean;
  onNavigateDivision: (key: DivisionKey) => void;
}) {
  const { t } = useLanguage();

  return (
    <div className="space-y-5">
      <div>
        <div className="mb-2 text-xs font-semibold uppercase text-muted">
          {t("workspaceShell.ceoCenter.intelligenceStateLabel")}
        </div>
        <div className="space-y-2">
          <IntelligenceStateRow
            label="Dairtna Poultry"
            state="provisional"
            detail={t("workspaceShell.ceoCenter.interpreterStatus")}
          />
          <IntelligenceStateRow
            label="Caesar Beverage"
            state="not_started"
            detail={t("workspaceShell.ceoCenter.phaseNotStarted")}
          />
          <IntelligenceStateRow
            label="Shared Corporate"
            state="not_started"
            detail={t("workspaceShell.ceoCenter.phaseNotStarted")}
          />
          <IntelligenceStateRow
            label="Multi-signal correlation"
            state="not_started"
            detail={t("workspaceShell.ceoCenter.correlationStatus")}
          />
        </div>
      </div>

      <div>
        <div className="mb-2 text-xs font-semibold uppercase text-muted">
          {t("workspaceShell.ceoCenter.divisionStatusLabel")}
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <DivisionStatusCard divisionKey="dairtna" onOpen={() => onNavigateDivision("dairtna")} />
          <DivisionStatusCard divisionKey="caesar" onOpen={() => onNavigateDivision("caesar")} />
          <DivisionStatusCard divisionKey="shared" onOpen={() => onNavigateDivision("shared")} />
        </div>
      </div>

      <div>
        <div className="mb-2 text-xs font-semibold uppercase text-muted">
          {t("workspaceShell.ceoCenter.traceabilityLabel")}
        </div>
        <div className="space-y-2">
          <TraceabilityCard
            source="Dairtna XLSX field report"
            signal="Mortality rate — computed from deaths / flock_size × 100"
            state="provisional"
            validation={t("workspaceShell.ceoCenter.thresholdsProvisional")}
          />
          <TraceabilityCard
            source="Not configured"
            signal="Production %, feed consumption, water trend, egg weight"
            state="not_started"
            validation="Phase 1 scope — not implemented"
          />
        </div>
      </div>

      <div className="rounded-md border border-line bg-surface p-3 text-xs leading-5 text-muted">
        <span className={`font-medium ${companyProfileActive ? "text-emerald-700" : "text-amber-700"}`}>
          {companyProfileActive ? t("companyContextActive") : t("companyContextInactive")}
        </span>
        <span className="mt-1 block">{t("workspaceShell.erpOneSource")}</span>
      </div>
    </div>
  );
}

function IntelligenceStateRow({
  label,
  state,
  detail,
}: {
  label: string;
  state: "provisional" | "validated" | "not_started" | "missing_baseline";
  detail: string;
}) {
  const { t } = useLanguage();

  const stateConfig: Record<typeof state, { badge: string; cls: string }> = {
    provisional: {
      badge: t("workspaceShell.ceoCenter.provisionalBadge"),
      cls: "border-amber-200 bg-amber-50 text-amber-700",
    },
    validated: {
      badge: t("workspaceShell.ceoCenter.validatedBadge"),
      cls: "border-emerald-200 bg-emerald-50 text-emerald-700",
    },
    not_started: {
      badge: t("workspaceShell.ceoCenter.notStartedBadge"),
      cls: "border-line bg-surface text-muted",
    },
    missing_baseline: {
      badge: t("workspaceShell.ceoCenter.missingBaselineBadge"),
      cls: "border-line bg-surface text-muted",
    },
  };

  const { badge, cls } = stateConfig[state];

  return (
    <div className="flex items-start justify-between gap-3 rounded-md border border-line bg-surface px-3 py-2">
      <div className="min-w-0">
        <div className="text-sm font-medium text-ink">{label}</div>
        <div className="mt-0.5 text-xs text-muted">{detail}</div>
      </div>
      <span className={`shrink-0 rounded border px-2 py-0.5 text-[11px] font-medium whitespace-nowrap ${cls}`}>
        {badge}
      </span>
    </div>
  );
}

function DivisionStatusCard({
  divisionKey,
  onOpen,
}: {
  divisionKey: DivisionKey;
  onOpen: () => void;
}) {
  const { language, t } = useLanguage();
  const config = getDivisionIntelligence(divisionKey);

  const stateByDivision: Record<DivisionKey, "provisional" | "not_started"> = {
    dairtna: "provisional",
    caesar: "not_started",
    shared: "not_started",
  };
  const state = stateByDivision[divisionKey];
  const stateLabel =
    state === "provisional"
      ? t("workspaceShell.ceoCenter.provisionalBadge")
      : t("workspaceShell.ceoCenter.notStartedBadge");
  const stateCls =
    state === "provisional"
      ? "border-amber-200 bg-amber-50 text-amber-700"
      : "border-line bg-surface text-muted";

  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-ink">
            {localizeWorkspaceText(config.title, language)}
          </div>
          <div className="mt-0.5 text-xs text-muted">{config.signals.length} signals</div>
        </div>
        <button
          type="button"
          onClick={onOpen}
          className="shrink-0 rounded border border-accent/30 bg-accent/10 px-2 py-1 text-xs text-accent hover:bg-accent/15"
        >
          {t("workspaceShell.ceoCenter.openDivision")}
        </button>
      </div>
      <div className="mt-2">
        <span className={`rounded border px-2 py-0.5 text-[11px] font-medium ${stateCls}`}>
          {stateLabel}
        </span>
      </div>
      <div className="mt-2 space-y-1">
        {config.signals.slice(0, 2).map((signal) => (
          <SignalRow key={signal.label} signal={signal} />
        ))}
      </div>
    </div>
  );
}

function TraceabilityCard({
  source,
  signal,
  state,
  validation,
}: {
  source: string;
  signal: string;
  state: "provisional" | "not_started" | "validated";
  validation: string;
}) {
  const { t } = useLanguage();
  const borderCls =
    state === "provisional"
      ? "border-amber-200 bg-amber-50"
      : state === "validated"
        ? "border-emerald-200 bg-emerald-50"
        : "border-line bg-surface";

  return (
    <div className={`rounded-md border p-3 text-xs ${borderCls}`}>
      <div className="space-y-1.5">
        <div className="flex gap-2">
          <span className="w-20 shrink-0 font-medium text-muted">{t("workspaceShell.ceoCenter.sourceFile")}</span>
          <span className="text-ink">{source}</span>
        </div>
        <div className="flex gap-2">
          <span className="w-20 shrink-0 font-medium text-muted">{t("workspaceShell.ceoCenter.extractedSignal")}</span>
          <span className="text-ink">{signal}</span>
        </div>
        <div className="flex gap-2">
          <span className="w-20 shrink-0 font-medium text-muted">{t("workspaceShell.ceoCenter.interpretationState")}</span>
          <span className="text-ink">{state}</span>
        </div>
        <div className="flex gap-2">
          <span className="w-20 shrink-0 font-medium text-muted">{t("workspaceShell.ceoCenter.pendingValidation")}</span>
          <span className="text-ink">{validation}</span>
        </div>
      </div>
    </div>
  );
}

function ExecutiveDivisionsSection({
  onNavigateDivision,
}: {
  onNavigateDivision: (key: DivisionKey) => void;
}) {
  const { language, t } = useLanguage();
  const divisionKeys: DivisionKey[] = ["dairtna", "caesar", "shared"];

  return (
    <div className="space-y-4">
      {isDemoModeEnabled() ? <DemoDataBanner /> : null}
      {divisionKeys.map((key) => {
        const config = getDivisionIntelligence(key);
        return (
          <div key={key} className="rounded-md border border-line bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="font-semibold text-ink">{localizeWorkspaceText(config.title, language)}</div>
                <div className="mt-0.5 text-xs text-muted">{localizeWorkspaceText(config.scope, language)}</div>
                <p className="mt-1 max-w-lg text-xs leading-5 text-muted">
                  {localizeWorkspaceText(config.subtitle, language)}
                </p>
              </div>
              <button
                type="button"
                onClick={() => onNavigateDivision(key)}
                className="shrink-0 rounded border border-accent/30 bg-accent/10 px-3 py-1.5 text-sm text-accent hover:bg-accent/15"
              >
                {t("workspaceShell.ceoCenter.openDivision")}
              </button>
            </div>
            <div className="mt-3 space-y-1">
              {config.signals.length > 0 ? (
                config.signals.map((signal) => <SignalRow key={signal.label} signal={signal} />)
              ) : (
                <EmptyIntelligenceNote />
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ExecutiveRisksSection() {
  const { language, t } = useLanguage();
  const divisionKeys: DivisionKey[] = ["dairtna", "caesar", "shared"];

  return (
    <div className="space-y-5">
      {isDemoModeEnabled() ? <DemoDataBanner /> : null}
      {divisionKeys.map((key) => {
        const config = getDivisionIntelligence(key);
        return (
          <div key={key}>
            <div className="mb-2 text-xs font-semibold uppercase text-muted">
              {localizeWorkspaceText(config.title, language)}
            </div>
            <InsightList items={config.risks} tone="risk" />
          </div>
        );
      })}
      <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
        {t("workspaceShell.ceoCenter.thresholdsProvisional")}
      </div>
    </div>
  );
}

function ExecutiveMemorySection({ companyProfileActive }: { companyProfileActive: boolean }) {
  const { t } = useLanguage();

  return (
    <div className="space-y-4">
      <div>
        <div className="mb-2 text-xs font-semibold uppercase text-muted">
          {t("workspaceShell.ceoCenter.baselineStatus")}
        </div>
        <div className="space-y-2">
          <IntelligenceStateRow
            label="Dairtna — mortality rate"
            state="provisional"
            detail={t("workspaceShell.ceoCenter.interpreterStatus")}
          />
          <IntelligenceStateRow
            label="Dairtna — production %, feed, water, egg weight"
            state="not_started"
            detail="Phase 1 scope — not implemented"
          />
          <IntelligenceStateRow
            label="Caesar Beverage — all metrics"
            state="not_started"
            detail={t("workspaceShell.ceoCenter.phaseNotStarted")}
          />
          <IntelligenceStateRow
            label="Shared Corporate — all metrics"
            state="not_started"
            detail={t("workspaceShell.ceoCenter.phaseNotStarted")}
          />
        </div>
      </div>
      <div className="rounded-md border border-line bg-surface px-3 py-2 text-xs text-muted">
        {t("workspaceShell.ceoCenter.correlationStatus")}
      </div>
      <div className="rounded-md border border-line bg-surface p-3 text-xs leading-5 text-muted">
        <span className={`font-medium ${companyProfileActive ? "text-emerald-700" : "text-amber-700"}`}>
          {companyProfileActive ? t("companyContextActive") : t("companyContextInactive")}
        </span>
        <span className="mt-1 block">{t("workspaceShell.erpOneSource")}</span>
      </div>
    </div>
  );
}

type DivisionTab = "overview" | "chat" | "events" | "files" | "insights";

function DivisionCommandCenter({
  token,
  companyId,
  divisionKey,
  activeDepartment,
  departments,
  displayDepartments,
  naturalCaptureDepartment,
  canSubmit,
  canUpload,
  canUseCeoWorkspace,
  canRecordDecisions,
  workspaceKey,
  chatTitle,
  awarenessRefreshKey,
  onCaptured,
}: {
  token: string | null;
  companyId: string | undefined;
  divisionKey: DivisionKey;
  activeDepartment: Department | null;
  departments: Department[];
  displayDepartments: Department[];
  naturalCaptureDepartment: Department | null;
  canSubmit: boolean;
  canUpload: boolean;
  canUseCeoWorkspace: boolean;
  canRecordDecisions: boolean;
  workspaceKey: string;
  chatTitle: string;
  awarenessRefreshKey: number;
  onCaptured: () => void;
}) {
  const [activeTab, setActiveTab] = useState<DivisionTab>("overview");
  const { t } = useLanguage();

  const tabs: { key: DivisionTab; label: string }[] = [
    { key: "overview", label: t("workspaceShell.divisionCenter.tabOverview") },
    { key: "chat", label: t("workspaceShell.divisionCenter.tabChat") },
    { key: "events", label: t("workspaceShell.divisionCenter.tabEvents") },
    { key: "files", label: t("workspaceShell.divisionCenter.tabFiles") },
    { key: "insights", label: t("workspaceShell.divisionCenter.tabInsights") },
  ];

  const config = getDivisionIntelligence(divisionKey);

  return (
    <section className="panel overflow-hidden">
      <div className="flex border-b border-line bg-white">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-3 text-sm font-medium transition ${
              activeTab === tab.key
                ? "border-b-2 border-accent text-accent"
                : "text-muted hover:text-ink"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="p-4">
        {activeTab === "overview" && <DivisionOverview config={config} />}

        {activeTab === "chat" &&
          (token && companyId ? (
            <ChatPanel
              token={token}
              companyId={companyId}
              workspaceKey={workspaceKey}
              title={chatTitle}
              department={activeDepartment}
              canRecordDecisions={canRecordDecisions}
            />
          ) : null)}

        {activeTab === "events" &&
          (divisionKey === "dairtna" ? (
            <div className="space-y-4">
              <NaturalOperationalCapturePanel
                token={token || ""}
                departments={departments}
                defaultDepartment={naturalCaptureDepartment}
                canSubmit={canSubmit}
                onCaptured={onCaptured}
              />
              <OperationalAwarenessPanel token={token || ""} refreshKey={awarenessRefreshKey} />
              <ManualOperationalEventPanel
                token={token || ""}
                departments={displayDepartments}
                defaultDepartment={activeDepartment}
                canSubmit={canSubmit}
              />
            </div>
          ) : (
            <div className="py-8 text-center text-sm text-muted">
              {t("workspaceShell.divisionCenter.eventsPlaceholder")}
            </div>
          ))}

        {activeTab === "files" && (
          <CompanyInputsPanel
            token={token || ""}
            department={activeDepartment}
            departments={displayDepartments}
            canSubmit={canSubmit}
            canUpload={canUpload}
            canAssignDepartment={canUseCeoWorkspace}
            onCaptured={onCaptured}
          />
        )}

        {activeTab === "insights" && (
          <div className="py-8 text-center">
            <div className="text-sm font-medium text-ink">
              {t("workspaceShell.divisionCenter.insightsPlaceholderTitle")}
            </div>
            <p className="mt-2 text-sm text-muted">
              {t("workspaceShell.divisionCenter.insightsPlaceholderText")}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

function DivisionOverview({ config }: { config: DivisionConfig }) {
  const { t } = useLanguage();

  return (
    <div className="space-y-4">
      {isDemoModeEnabled() ? <DemoDataBanner /> : null}
      <IntelligenceSection title={t("workspaceShell.liveSignals")}>
        <div className="space-y-2">
          {config.signals.length > 0 ? (
            config.signals.map((signal) => <SignalRow key={signal.label} signal={signal} />)
          ) : (
            <EmptyIntelligenceNote />
          )}
        </div>
      </IntelligenceSection>
      <IntelligenceSection title="Detected risks">
        <InsightList items={config.risks} tone="risk" />
      </IntelligenceSection>
      <IntelligenceSection title="Suggested actions">
        <InsightList items={config.actions} tone="neutral" />
      </IntelligenceSection>
    </div>
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
        {isDemoModeEnabled() ? <DemoDataBanner /> : null}

        <IntelligenceSection title="Active division">
          <div className="rounded-md border border-line bg-surface px-3 py-2 text-sm text-ink">
            {localizeWorkspaceText(config.scope, language)}
          </div>
        </IntelligenceSection>

        <IntelligenceSection title={t("workspaceShell.liveSignals")}>
          <div className="space-y-2">
            {config.signals.length > 0 ? (
              config.signals.map((signal) => <SignalRow key={signal.label} signal={signal} />)
            ) : (
              <EmptyIntelligenceNote />
            )}
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
          {config.relatedFiles.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {config.relatedFiles.map((file) => (
                <span key={file} className="rounded-md border border-line bg-surface px-2 py-1 text-xs text-muted">
                  {localizeWorkspaceText(file, language)}
                </span>
              ))}
            </div>
          ) : (
            <EmptyIntelligenceNote />
          )}
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

function DemoDataBanner() {
  const { t } = useLanguage();
  return (
    <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-800">
      {t("demoDataBadge")} — {t("demoDataBannerText")}
    </div>
  );
}

function EmptyIntelligenceNote() {
  const { t } = useLanguage();
  return <p className="text-sm leading-6 text-muted">{t("notYetComputed")}</p>;
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

  if (items.length === 0) {
    return <EmptyIntelligenceNote />;
  }

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
    return getDivisionIntelligence(workspace.divisionKey);
  }
  if (workspace.kind === "settings") {
    return {
      ...getDivisionIntelligence("memory"),
      title: "Settings",
      subtitle: "Company context and organizational intelligence controls for NAWA.",
      scope: "Jannat Al-Firdaws settings",
    };
  }
  return getDivisionIntelligence(workspace.kind);
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
    "Executive Command Center": "workspaceShell.ceoCenter.sectionLabel",
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
    "Company Inputs": "workspaceShell.workspaces.inputs.label",
    "Excel, PDF, text updates": "workspaceShell.workspaces.inputs.description",
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
