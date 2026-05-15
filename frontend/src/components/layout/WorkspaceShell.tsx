"use client";

import { useAuth } from "@/components/auth/AuthProvider";

const workforceItems = ["CEO AI", "Sales AI", "Finance AI", "Marketing AI", "Operations AI"];

export function WorkspaceShell() {
  const { me, logout } = useAuth();
  const permissions = me?.role.permissions ?? [];

  return (
    <main className="min-h-screen bg-surface text-ink">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div>
            <div className="text-sm font-semibold tracking-wide text-ink">AIMX</div>
            <div className="text-xs text-muted">AI Workforce Platform</div>
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
        <aside className="panel h-fit p-3">
          <div className="px-2 pb-2 text-xs font-semibold uppercase text-muted">Workspace</div>
          <nav className="space-y-1">
            {workforceItems.map((item, index) => (
              <button
                key={item}
                className={`w-full rounded-md px-3 py-2 text-left text-sm ${
                  index === 0
                    ? "bg-blue-50 font-medium text-accent"
                    : "text-ink hover:bg-surface"
                }`}
                type="button"
              >
                {item}
              </button>
            ))}
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
                <div className="text-xs font-semibold uppercase text-muted">Active agent</div>
                <h1 className="mt-1 text-xl font-semibold text-ink">CEO AI Workspace</h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
                  Company-wide AI workspace shell is ready. Chat, departments, and files will
                  plug into this operational dashboard in the next frontend phases.
                </p>
              </div>
              <div className="rounded-md border border-line bg-surface px-3 py-2 text-xs text-muted">
                Backend: {process.env.NEXT_PUBLIC_AIMX_API_URL || "http://localhost:8000"}
              </div>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <StatusPanel title="Auth" value="Connected" detail="/auth/login + /auth/me" />
            <StatusPanel title="Workspace" value={me?.company.slug ?? "Ready"} detail="Tenant scoped" />
            <StatusPanel title="Next" value="Chat MVP" detail="/ai/chat integration pending" />
          </div>
        </section>
      </div>
    </main>
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
