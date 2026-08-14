import { useTranslations } from "next-intl";
import { Sparkles, ShieldCheck, BarChart3, ArrowRight } from "lucide-react";
import { Link } from "@/lib/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function Hero() {
  const t = useTranslations("hero");

  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-b from-white via-background to-background"
      />
      <div className="mx-auto flex max-w-6xl flex-col items-center px-4 py-20 text-center sm:px-6 sm:py-28">
        <Badge variant="accent" className="mb-6 gap-1.5">
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          {t("badge")}
        </Badge>
        <h1 className="max-w-3xl text-4xl font-bold leading-tight tracking-tight text-primary sm:text-5xl md:text-6xl">
          {t("title")}
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-muted-foreground">
          {t("subtitle")}
        </p>
        <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row">
          <Button asChild size="lg" variant="accent" className="w-full sm:w-auto">
            <Link href="/valuation">
              {t("primaryCta")}
              <ArrowRight className="rtl:rotate-180" aria-hidden="true" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="w-full sm:w-auto">
            <Link href="#how-it-works">{t("secondaryCta")}</Link>
          </Button>
        </div>
        <ul className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm font-medium text-muted-foreground">
          {(["trustPoints"] as const).flatMap((key) =>
            t.raw(key).map((point: string) => (
              <li key={point} className="flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-accent" aria-hidden="true" />
                {point}
              </li>
            )),
          )}
        </ul>
      </div>
    </section>
  );
}

export function TrustSection() {
  const t = useTranslations("trust");
  const items = t.raw("items") as Array<{ title: string; description: string }>;
  const icons = [BarChart3, Sparkles, ShieldCheck];

  return (
    <section className="bg-card">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-primary sm:text-4xl">
            {t("title")}
          </h2>
          <p className="mt-3 text-muted-foreground">{t("subtitle")}</p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {items.map((item, i) => {
            const Icon = icons[i % icons.length];
            return (
              <div
                key={item.title}
                className="rounded-xl border bg-background p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {item.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export function HowItWorks() {
  const t = useTranslations("how");
  const steps = t.raw("steps") as Array<{ title: string; description: string }>;
  const numbers = ["01", "02", "03"];

  return (
    <section id="how-it-works" className="scroll-mt-24">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-primary sm:text-4xl">
            {t("title")}
          </h2>
          <p className="mt-3 text-muted-foreground">{t("subtitle")}</p>
        </div>
        <ol className="mt-12 grid gap-6 md:grid-cols-3">
          {steps.map((step, i) => (
            <li
              key={step.title}
              className="relative rounded-xl border bg-card p-6 shadow-sm"
            >
              <span className="text-4xl font-bold text-gold/40">
                {numbers[i]}
              </span>
              <h3 className="mt-3 text-lg font-semibold text-foreground">
                {step.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {step.description}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function FinalCta() {
  const t = useTranslations("finalCta");

  return (
    <section className="bg-primary">
      <div className="mx-auto flex max-w-6xl flex-col items-center px-4 py-20 text-center sm:px-6">
        <h2 className="max-w-2xl text-3xl font-bold tracking-tight text-primary-foreground sm:text-4xl">
          {t("title")}
        </h2>
        <p className="mt-3 text-lg text-primary-foreground/80">{t("subtitle")}</p>
        <Button asChild size="lg" variant="accent" className="mt-8">
          <Link href="/valuation">{t("cta")}</Link>
        </Button>
      </div>
    </section>
  );
}