"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { FilesPanel } from "@/components/files/FilesPanel";
import { ApiError } from "@/lib/api/client";
import { listDepartments } from "@/lib/api/departments";
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

  const activeDepartment = useMemo(() => {
    if (activeWorkspace.kind !== "department") {
      return null;
    }
    return departments.find((department) => department.id === activeWorkspace.departmentId) ?? null;
  }, [activeWorkspace, departments]);

  const activeTitle = activeDepartment
    ? getDepartmentAgentLabel(activeDepartment)
    : "CEO AI Workspace";
  const activeScope = activeDepartment ? "Department-scoped" : "Company-wide";
  const activeDescription = activeDepartment
    ? activeDepartment.description || `${activeDepartment.name} workspace is ready for chat integration.`
    : "Company-wide AI workspace for executive planning, cross-department priorities, and demo-ready AIMX decisions.";
  const activeWorkspaceKey = activeDepartment ? `department-${activeDepartment.id}` : "ceo";

  return (
    <main className="min-h-screen bg-surface text-ink">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md border border-line bg-ink text-sm font-semibold text-white">
              AX
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide text-ink">AIMX</div>
              <div className="text-xs text-muted">AI Workforce Platform</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <div className="text-sm font-medium">{me?.company.name}</div>
              <div className="text-xs text-muted">{me?.user.email}</div>
            </div>
            <button className="button-secondary" type="button" onClick={logout}>
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-4 px-4 py-4 sm:px-6 lg:grid-cols-[240px_1fr]">
        <aside className="panel h-fit p-3 lg:sticky lg:top-4">
          <div className="px-2 pb-2 text-xs font-semibold uppercase text-muted">Workspace</div>
          <nav className="space-y-1">
            <SidebarItem
              label="CEO AI"
              description="Executive command"
              badge="CEO"
              active={activeWorkspace.kind === "ceo"}
              onClick={() => setActiveWorkspace({ kind: "ceo" })}
            />

            <div className="px-2 pt-3 text-xs font-semibold uppercase text-muted">Departments</div>

            {departmentStatus === "loading" ? (
              <div className="px-3 py-2 text-sm text-muted">Loading departments...</div>
            ) : null}

            {departmentStatus === "blocked" ? (
              <div className="rounded-md border border-line bg-surface px-3 py-2 text-sm text-muted">
                Department list unavailable for this role.
              </div>
            ) : null}

            {departmentStatus === "error" ? (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {departmentError}
              </div>
            ) : null}

            {departmentStatus === "ready" && departments.length === 0 ? (
              <div className="rounded-md border border-dashed border-line bg-surface px-3 py-2">
                <div className="text-sm font-medium text-ink">No departments yet</div>
                <div className="mt-1 text-xs leading-5 text-muted">
                  Run the demo seed to unlock Sales, Finance, Marketing, and Operations workspaces.
                </div>
              </div>
            ) : null}

            {departments.map((department) => {
              const canUseDepartment = canUseAgent(permissions, department.department_type);
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
          <div className="mt-4 border-t border-line px-2 pt-3">
            <div className="text-xs font-semibold uppercase text-muted">Role</div>
            <div className="mt-1 text-sm font-medium">{me?.role.name}</div>
            <div className="mt-1 text-xs text-muted">{permissions.length} permissions available</div>
          </div>
        </aside>

        <section className="space-y-4">
          <div className="panel p-4">
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
              <div>
                <div className="text-xs font-semibold uppercase text-muted">Live AI workforce</div>
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <h1 className="text-xl font-semibold text-ink">{activeTitle}</h1>
                  <span className="rounded-md border border-line bg-surface px-2 py-1 text-xs font-medium text-muted">
                    {activeDepartment ? activeDepartment.name : "Executive"}
                  </span>
                </div>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
                  {activeDescription}
                </p>
              </div>
              <div className="rounded-md border border-line bg-surface px-3 py-2 text-xs text-muted">
                Scope: {activeScope}
              </div>
            </div>
          </div>

          <QuickStartPanel
            activeTitle={activeTitle}
            canReadFiles={canReadFiles}
          />

          <div className="grid gap-3 md:grid-cols-3">
            <StatusPanel title="Identity" value="Verified" detail="Auth and role loaded" />
            <StatusPanel
              title="Departments"
              value={canReadDepartments ? String(departments.length) : "Locked"}
              detail={canReadDepartments ? "AI workspaces available" : "Missing departments.read"}
            />
            <StatusPanel
              title="Tenant"
              value={me?.company.slug ?? "Ready"}
              detail="Company-isolated context"
            />
          </div>

          {token && me ? (
            <div className={canReadFiles ? "grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]" : ""}>
              <ChatPanel
                token={token}
                companyId={me.company.id}
                workspaceKey={activeWorkspaceKey}
                title={activeTitle}
                department={activeDepartment}
              />
              {canReadFiles ? (
                <FilesPanel token={token} departments={departments} />
              ) : null}
            </div>
          ) : null}
        </section>
      </div>
    </main>
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
          <div className="text-xs font-semibold uppercase text-muted">Demo quick start</div>
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
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-line bg-white text-[11px] font-semibold text-ink">
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
          ? "bg-blue-50 font-medium text-accent"
          : disabled
            ? "cursor-not-allowed bg-white text-muted opacity-70"
            : "text-ink hover:bg-surface"
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
              ? "border-blue-200 bg-white text-accent"
              : "border-line bg-surface text-muted"
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
          <span className="mt-0.5 block truncate text-xs text-muted">{description}</span>
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
