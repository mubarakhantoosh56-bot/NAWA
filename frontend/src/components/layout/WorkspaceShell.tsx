"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { FilesPanel } from "@/components/files/FilesPanel";
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
        setDepartmentError(caught instanceof ApiError ? caught.detail : "Unable to load departments.");
      });

    return () => {
      isMounted = false;
    };
  }, [canReadDepartments, token]);

  const displayDepartments = departments.length > 0 ? departments : DEMO_DEPARTMENTS;
  const isDemoDataset = departments.length === 0;

  const activeDepartment = useMemo(() => {
    if (activeWorkspace.kind !== "department") {
      return null;
    }
    return displayDepartments.find((department) => department.id === activeWorkspace.departmentId) ?? null;
  }, [activeWorkspace, displayDepartments]);

  const demoWorkspaceKey = getDemoWorkspaceKey(activeDepartment);

  const activeTitle = activeDepartment
    ? getDepartmentAgentLabel(activeDepartment)
    : "CEO AI Workspace";
  const activeScope = activeDepartment ? "Department-scoped" : "Company-wide";
  const activeDescription = activeDepartment
    ? activeDepartment.description || `${activeDepartment.name} workspace is ready for chat integration.`
    : "Company-wide AI workspace for executive planning, cross-department priorities, and demo-ready NAWA decisions.";
  const activeWorkspaceKey = activeDepartment ? `department-${activeDepartment.id}` : "ceo";

  return (
    <main className="min-h-screen text-ink">
      <header className="border-b border-white/10 bg-executive text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md border border-white/15 bg-white/10 text-sm font-semibold text-white">
              ن
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide text-white">NAWA · نواة</div>
              <div className="text-xs text-white/60">AI Workforce Platform</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <div className="text-sm font-medium">{me?.company.name || DEMO_COMPANY.name}</div>
              <div className="text-xs text-white/60">{me?.user.email || DEMO_COMPANY.email}</div>
            </div>
            <button className="rounded-md border border-white/15 bg-white/10 px-3 py-2 text-sm font-medium text-white transition hover:bg-white/15" type="button" onClick={logout}>
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-4 px-4 py-4 sm:px-6 lg:grid-cols-[260px_1fr]">
        <aside className="command-panel h-fit p-3 lg:sticky lg:top-4">
          <div className="px-2 pb-2 text-xs font-semibold uppercase text-white/60">Workspace</div>
          <nav className="space-y-1">
            <SidebarItem
              label="CEO AI"
              description="Executive command"
              badge="CEO"
              active={activeWorkspace.kind === "ceo"}
              onClick={() => setActiveWorkspace({ kind: "ceo" })}
            />

            <div className="px-2 pt-3 text-xs font-semibold uppercase text-white/60">Departments</div>

            {departmentStatus === "loading" ? (
              <div className="rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/70">
                <span className="inline-flex items-center gap-2">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-gold" />
                  Loading departments...
                </span>
              </div>
            ) : null}

            {departmentStatus === "blocked" ? (
              <div className="rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/70">
                Department list unavailable for this role.
              </div>
            ) : null}

            {departmentStatus === "error" ? (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {departmentError}
              </div>
            ) : null}

            {isDemoDataset ? (
              <div className="rounded-md border border-white/10 bg-white/5 px-3 py-2">
                <div className="text-sm font-medium text-white">Investor demo dataset</div>
                <div className="mt-1 text-xs leading-5 text-white/55">
                  Populated with realistic enterprise workspaces.
                </div>
              </div>
            ) : null}

            {displayDepartments.map((department) => {
              const canUseDepartment = isDemoDataset || canUseAgent(permissions, department.department_type);
              return (
                <SidebarItem
                  key={department.id}
                  label={getDepartmentAgentLabel(department)}
                  description={department.name}
                  badge={getDepartmentBadge(department)}
                  active={
                    activeWorkspace.kind === "department" &&
                    activeWorkspace.departmentId === department.id
                  }
                  disabled={!canUseDepartment || !department.ai_agent_enabled}
                  lockLabel={!canUseDepartment ? "Locked" : "Off"}
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
            <div className="text-xs font-semibold uppercase text-white/60">Role</div>
            <div className="mt-1 text-sm font-medium text-white">{me?.role.name || DEMO_COMPANY.role}</div>
            <div className="mt-1 text-xs text-white/60">{permissions.length} permissions available</div>
          </div>
        </aside>

        <section className="space-y-4">
          <div className="command-panel p-4">
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
              <div>
                <div className="text-xs font-semibold uppercase text-white/60">Live AI workforce</div>
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <h1 className="text-xl font-semibold text-white">{activeTitle}</h1>
                  <span className="rounded-md border border-white/10 bg-white/10 px-2 py-1 text-xs font-medium text-white/70">
                    {activeDepartment ? activeDepartment.name : "Executive"}
                  </span>
                </div>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-white/70">
                  {activeDescription}
                </p>
              </div>
              <div className="rounded-md border border-white/10 bg-white/10 px-3 py-2 text-xs text-white/70">
                Scope: {activeScope}
              </div>
            </div>
          </div>

          <QuickStartPanel
            activeTitle={activeTitle}
            canReadFiles={canReadFiles}
          />

          <div className="grid gap-3 md:grid-cols-3">
            {DEMO_KPIS[demoWorkspaceKey].map((kpi) => (
              <StatusPanel key={kpi.title} title={kpi.title} value={kpi.value} detail={kpi.detail} />
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
              {canReadFiles ? (
                <FilesPanel token={token} departments={displayDepartments} />
              ) : null}
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}

function DemoBriefingPanel({ workspaceKey }: { workspaceKey: keyof typeof DEMO_REPORTS }) {
  return (
    <section className="panel p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-2xl">
          <div className="executive-label">Executive summary</div>
          <p className="mt-2 text-sm leading-6 text-ink">{DEMO_EXECUTIVE_SUMMARIES[workspaceKey]}</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 lg:min-w-[520px]">
          {DEMO_REPORTS[workspaceKey].map((report) => (
            <article key={report.title} className="rounded-md border border-line bg-surface px-3 py-2.5">
              <div className="text-sm font-semibold text-ink">{report.title}</div>
              <p className="mt-1 text-xs leading-5 text-muted">{report.detail}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function QuickStartPanel({
  activeTitle,
  canReadFiles,
}: {
  activeTitle: string;
  canReadFiles: boolean;
}) {
  return (
    <section className="panel p-3">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="executive-label">Demo quick start</div>
          <div className="mt-1 text-sm font-medium text-ink">
            Select an AI worker, review knowledge files, then ask a decision question.
          </div>
        </div>
        <div className="grid gap-2 text-xs text-muted sm:grid-cols-3 lg:min-w-[520px]">
          <QuickStartStep value="1" label={activeTitle} />
          <QuickStartStep
            value="2"
            label={canReadFiles ? "Review knowledge files" : "Files locked"}
          />
          <QuickStartStep value="3" label="Use a suggested prompt" />
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
  return (
    <button
      className={`w-full rounded-md px-3 py-2 text-left text-sm transition ${
        active
          ? "bg-white/10 font-medium text-white"
          : disabled
            ? "cursor-not-allowed bg-white/5 text-white/50 opacity-70"
            : "text-white/80 hover:bg-white/10"
      }`}
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={disabled ? "This workspace is not available for your current role." : undefined}
    >
      <span className="flex items-start gap-2">
        <span
          className={`mt-0.5 flex h-7 w-8 shrink-0 items-center justify-center rounded-md border text-[11px] font-semibold ${
            active
              ? "border-gold/50 bg-gold/15 text-gold"
              : "border-white/10 bg-white/5 text-white/60"
          }`}
        >
          {badge}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center justify-between gap-2">
            <span className="truncate">{label}</span>
            {disabled ? (
              <span className="rounded border border-line px-1.5 py-0.5 text-[10px] uppercase text-muted">
                {lockLabel || "Locked"}
              </span>
            ) : null}
          </span>
          <span className="mt-0.5 block truncate text-xs text-white/50">{description}</span>
        </span>
      </span>
    </button>
  );
}

function StatusPanel({
  title,
  value,
  detail,
}: {
  title: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="panel p-4">
      <div className="text-xs font-semibold uppercase text-muted">{title}</div>
      <div className="mt-2 text-base font-semibold text-ink">{value}</div>
      <div className="mt-1 text-sm text-muted">{detail}</div>
    </div>
  );
}

function getDepartmentAgentLabel(department: Department): string {
  return departmentTypeLabels[department.department_type] || `${department.name} AI`;
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
