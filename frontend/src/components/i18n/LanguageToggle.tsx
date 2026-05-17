"use client";

import { useLanguage } from "@/components/i18n/LanguageProvider";
import { cn } from "@/lib/utils";

export function LanguageToggle() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <div className="inline-flex rounded-md border border-white/15 bg-white/10 p-0.5">
      <button
        className={cn(
          "rounded px-2.5 py-1 text-xs font-semibold transition",
          language === "ar" ? "bg-white text-executive" : "text-white/65 hover:text-white",
        )}
        type="button"
        onClick={() => setLanguage("ar")}
      >
        {t("languageArabic")}
      </button>
      <button
        className={cn(
          "rounded px-2.5 py-1 text-xs font-semibold transition",
          language === "en" ? "bg-white text-executive" : "text-white/65 hover:text-white",
        )}
        type="button"
        onClick={() => setLanguage("en")}
      >
        {t("languageEnglish")}
      </button>
    </div>
  );
}
