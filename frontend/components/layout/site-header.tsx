import { useTranslations } from "next-intl";
import { Link } from "@/lib/navigation";
import { Logo } from "./logo";
import { LanguageSwitcher } from "./language-switcher";
import { Button } from "@/components/ui/button";

export function SiteHeader() {
  const t = useTranslations("nav");

  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Logo />
        <nav className="hidden items-center gap-6 text-sm font-medium text-muted-foreground md:flex">
          <Link
            href="/"
            className="transition-colors hover:text-primary"
          >
            {t("home")}
          </Link>
          <Link
            href="/valuation"
            className="transition-colors hover:text-primary"
          >
            {t("valuation")}
          </Link>
          <Link
            href="/recommendations"
            className="transition-colors hover:text-primary"
          >
            {t("recommendations")}
          </Link>
        </nav>
        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          <Button asChild size="default" variant="accent">
            <Link href="/valuation">{t("valueCta")}</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}