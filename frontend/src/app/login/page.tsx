"use client";

import { LoginForm } from "@/components/auth/LoginForm";
import { useLanguage } from "@/components/i18n/LanguageProvider";
import { LanguageToggle } from "@/components/i18n/LanguageToggle";

export default function LoginPage() {
  const { t } = useLanguage();

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-8">
      <section className="grid w-full max-w-5xl overflow-hidden rounded-md border border-white/10 bg-white shadow-command md:grid-cols-[1fr_420px]">
        <div className="hidden bg-executive p-8 text-white md:block">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-md border border-white/15 bg-white/10 text-lg font-semibold">
                N
              </div>
              <div>
                <div className="text-sm font-semibold">{t("brandNawa")}</div>
                <div className="text-xs text-white/60">{t("aiWorkforcePlatform")}</div>
              </div>
            </div>
            <LanguageToggle />
          </div>
          <h1 className="mt-8 max-w-md text-3xl font-semibold leading-tight">{t("signInTitle")}</h1>
          <p className="mt-4 max-w-md text-sm leading-6 text-white/70">{t("signInSubtitle")}</p>
          <div className="mt-8 grid gap-3 text-sm">
            <div className="rounded-md border border-white/10 bg-white/5 p-3">{t("signInCardExecutive")}</div>
            <div className="rounded-md border border-white/10 bg-white/5 p-3">{t("signInCardDepartments")}</div>
            <div className="rounded-md border border-white/10 bg-white/5 p-3">{t("signInCardDemo")}</div>
          </div>
        </div>

        <div className="p-6 sm:p-8">
          <div className="mb-6">
            <div className="mb-4 flex items-center justify-between md:hidden">
              <div className="text-sm font-semibold text-accent">{t("brandNawa")}</div>
              <div className="[&>div]:border-line [&>div]:bg-surface [&_button]:text-ink/70 [&_button.bg-white]:bg-accent [&_button.bg-white]:text-white">
                <LanguageToggle />
              </div>
            </div>
            <h2 className="mt-2 text-xl font-semibold text-ink">{t("companyLogin")}</h2>
            <p className="mt-2 text-sm text-muted">{t("companyLoginHint")}</p>
          </div>
          <LoginForm />
        </div>
      </section>
    </main>
  );
}
