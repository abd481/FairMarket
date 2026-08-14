"use client";

import { useLocale, useTranslations } from "next-intl";
import { Languages } from "lucide-react";
import { usePathname, useRouter } from "@/lib/navigation";
import { useTransition } from "react";

export function LanguageSwitcher() {
  const locale = useLocale();
  const t = useTranslations("language");
  const pathname = usePathname();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const otherLocale = locale === "en" ? "ar" : "en";

  function switchLocale() {
    startTransition(() => {
      router.replace(pathname, { locale: otherLocale });
    });
  }

  return (
    <button
      type="button"
      onClick={switchLocale}
      disabled={isPending}
      aria-label="Switch language"
      className="inline-flex h-9 items-center gap-1.5 rounded-md border border-input bg-card px-3 text-sm font-medium text-secondary-foreground shadow-sm transition-colors hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50"
    >
      <Languages className="h-4 w-4" aria-hidden="true" />
      <span dir={otherLocale === "ar" ? "rtl" : "ltr"}>{t("label")}</span>
    </button>
  );
}