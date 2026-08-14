import { useTranslations } from "next-intl";
import { Link } from "@/lib/navigation";
import { Logo } from "./logo";

export function SiteFooter() {
  const t = useTranslations("footer");
  const tNav = useTranslations("nav");

  return (
    <footer className="border-t bg-card">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="flex flex-col gap-8 md:flex-row md:items-start md:justify-between">
          <div className="max-w-xs space-y-3">
            <Logo />
            <p className="text-sm text-muted-foreground">{t("tagline")}</p>
          </div>
          <div className="grid grid-cols-1 gap-8 text-sm sm:grid-cols-2">
            <div className="space-y-2">
              <p className="font-semibold text-foreground">{t("links")}</p>
              <ul className="space-y-2 text-muted-foreground">
                <li>
                  <Link href="/valuation" className="transition-colors hover:text-primary">
                    {tNav("valuation")}
                  </Link>
                </li>
                <li>
                  <Link href="/recommendations" className="transition-colors hover:text-primary">
                    {tNav("recommendations")}
                  </Link>
                </li>
              </ul>
            </div>
            <div className="space-y-2">
              <p className="font-semibold text-foreground">{t("legal")}</p>
              <p className="text-muted-foreground">{t("disclaimer")}</p>
            </div>
          </div>
        </div>
        <div className="mt-10 border-t pt-6 text-xs text-muted-foreground">
          © {new Date().getFullYear()} FairMarket. {t("rights")}
        </div>
      </div>
    </footer>
  );
}