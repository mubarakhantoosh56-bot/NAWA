import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-surface px-4 py-8">
      <section className="grid w-full max-w-5xl overflow-hidden rounded-md border border-line bg-white shadow-panel md:grid-cols-[1fr_420px]">
        <div className="hidden border-r border-line bg-surface p-8 md:block">
          <div className="text-sm font-semibold text-accent">NAWA · نواة</div>
          <h1 className="mt-6 max-w-md text-3xl font-semibold leading-tight text-ink">
            Sign in to the Arabic-first AI workforce workspace.
          </h1>
          <p className="mt-4 max-w-md text-sm leading-6 text-muted">
            Access CEO and department AI workspaces backed by company knowledge,
            RBAC, and tenant-scoped backend services.
          </p>
          <div className="mt-8 grid gap-3 text-sm text-ink">
            <div className="rounded-md border border-line bg-white p-3">Company workspace</div>
            <div className="rounded-md border border-line bg-white p-3">Department AI shell</div>
            <div className="rounded-md border border-line bg-white p-3">Demo-ready auth flow</div>
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
