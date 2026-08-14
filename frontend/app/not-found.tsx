import { getTranslations } from "next-intl/server";
import { Link } from "@/lib/navigation";
import { Button } from "@/components/ui/button";
import { routing } from "@/i18n/routing";

export default async function NotFoundPage() {
  const t = await getTranslations({ locale: routing.defaultLocale, namespace: "notFound" });

  return (
    <div className="mx-auto flex max-w-md flex-col items-center px-4 py-24 text-center">
      <p className="text-6xl font-bold text-primary/20">404</p>
      <h1 className="mt-4 text-2xl font-bold text-primary">{t("title")}</h1>
      <p className="mt-2 text-muted-foreground">{t("description")}</p>
      <Button asChild variant="accent" className="mt-8">
        <Link href="/">{t("cta")}</Link>
      </Button>
    </div>
  );
}