import { ar } from "@/lib/i18n/dictionaries/ar";
import { en } from "@/lib/i18n/dictionaries/en";

export type Language = "en" | "ar";

type TranslationValue = string | { [key: string]: TranslationValue };
type TranslationDictionary = { [key: string]: TranslationValue };

export const LANGUAGE_STORAGE_KEY = "nawa.language";

export const dictionaries: Record<Language, TranslationDictionary> = {
  en,
  ar,
};

export type TranslationKey = string;

export function isLanguage(value: string | null): value is Language {
  return value === "en" || value === "ar";
}

export function directionFor(language: Language) {
  return language === "ar" ? "rtl" : "ltr";
}

export function translate(language: Language, key: TranslationKey): string {
  return resolveTranslation(dictionaries[language], key) ?? key;
}

function resolveTranslation(dictionary: TranslationDictionary, key: string): string | null {
  const direct = dictionary[key as keyof TranslationDictionary];
  if (typeof direct === "string") {
    return direct;
  }

  const parts = key.split(".");
  let current: TranslationValue | undefined = dictionary;
  for (const part of parts) {
    if (!current || typeof current === "string") {
      return null;
    }
    current = current[part];
  }

  return typeof current === "string" ? current : null;
}
