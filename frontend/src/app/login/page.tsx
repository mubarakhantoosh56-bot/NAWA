import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-8">
      <section className="grid w-full max-w-5xl overflow-hidden rounded-md border border-white/10 bg-white shadow-command md:grid-cols-[1fr_420px]">
        <div className="hidden bg-executive p-8 text-white md:block">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md border border-white/15 bg-white/10 text-lg font-semibold">
              ن
            </div>
            <div>
              <div className="text-sm font-semibold">NAWA · نواة</div>
              <div className="text-xs text-white/60">AI Workforce Platform</div>
            </div>
          </div>
          <h1 className="mt-8 max-w-md text-3xl font-semibold leading-tight">
            Sign in to the Arabic-first AI workforce workspace.
          </h1>
          <p className="mt-4 max-w-md text-sm leading-6 text-white/70">
            Access CEO and department AI workspaces backed by company knowledge,
            RBAC, and tenant-scoped backend services.
          </p>
          <div className="mt-8 grid gap-3 text-sm">
            <div className="rounded-md border border-white/10 bg-white/5 p-3">Executive command workspace</div>
            <div className="rounded-md border border-white/10 bg-white/5 p-3">Department AI workforce</div>
            <div className="rounded-md border border-white/10 bg-white/5 p-3">Arabic-first enterprise identity</div>
          </div>
        </div>

        <div className="p-6 sm:p-8">
          <div className="mb-6">
            <div className="text-sm font-semibold text-accent md:hidden">NAWA · نواة</div>
            <h2 className="mt-2 text-xl font-semibold text-ink">Company login</h2>
            <p className="mt-2 text-sm text-muted">
              Use the Atlas demo tenant or your local NAWA company credentials.
            </p>
          </div>
          <LoginForm />
        </div>
      </section>
    </main>
  );
}
