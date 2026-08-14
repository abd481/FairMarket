"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import {
  Sparkles,
  MapPin,
  Building2,
  Ruler,
  BedDouble,
  Bath,
  ArrowLeft,
  ArrowRight,
  Home,
  RotateCcw,
} from "lucide-react";
import { Link, useRouter } from "@/lib/navigation";
import { useValuationState } from "@/lib/valuation-store";
import { formatEGP, formatNumber, formatPricePerSqm } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useLocale } from "next-intl";

function PriceResultCard({
  predicted,
  lower,
  upper,
  perSqm,
}: {
  predicted: number;
  lower: number;
  upper: number;
  perSqm: string;
}) {
  const t = useTranslations("result");
  const locale = useLocale();
  const ArrowIcon = locale === "ar" ? ArrowLeft : ArrowRight;

  return (
    <div className="rounded-2xl bg-primary p-6 text-primary-foreground shadow-lg sm:p-8">
      <Badge variant="accent" className="mb-4 gap-1.5">
        <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
        {t("badge")}
      </Badge>

      <p className="text-sm font-medium text-primary-foreground/70">
        {t("predictedLabel")}
      </p>
      <p className="mt-2 text-4xl font-bold tracking-tight sm:text-5xl">
        {formatEGP(predicted, locale)}
      </p>

      <div className="mt-6 border-t border-primary-foreground/15 pt-5">
        <p className="text-sm font-medium text-primary-foreground/70">
          {t("rangeLabel")}
        </p>
        <p className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1 text-2xl font-bold tracking-tight sm:text-3xl">
          <span>{formatEGP(lower, locale)}</span>
          <ArrowIcon className="h-5 w-5 text-primary-foreground/50" aria-hidden="true" />
          <span>{formatEGP(upper, locale)}</span>
        </p>
      </div>

      <div className="mt-6 flex items-center gap-2 text-sm text-primary-foreground/80">
        <Ruler className="h-4 w-4" aria-hidden="true" />
        <span>
          {t("pricePerSqm")}: <span className="font-semibold text-primary-foreground">{perSqm}</span>
        </span>
      </div>
    </div>
  );
}

function DetailRow({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-background px-4 py-3">
      <span className="text-muted-foreground">{icon}</span>
      <div className="flex flex-col">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-sm font-semibold text-foreground">{value}</span>
      </div>
    </div>
  );
}

export function ResultView() {
  const t = useTranslations("result");
  const locale = useLocale();
  const router = useRouter();
  const { state } = useValuationState();

  if (!state) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center px-4 py-20 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-secondary">
          <Home className="h-7 w-7 text-primary" aria-hidden="true" />
        </div>
        <h1 className="mt-6 text-2xl font-bold text-primary">{t("emptyTitle")}</h1>
        <p className="mt-2 text-muted-foreground">{t("emptyDescription")}</p>
        <Button asChild variant="accent" className="mt-8">
          <Link href="/valuation">{t("valueAnother")}</Link>
        </Button>
      </div>
    );
  }

  const { request, result } = state;
  const perSqm = formatPricePerSqm(result.predicted_price, request.area, locale);

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6 sm:py-16">
      <h1 className="text-center text-3xl font-bold tracking-tight text-primary">
        {t("title")}
      </h1>

      <div className="mt-8">
        <PriceResultCard
          predicted={result.predicted_price}
          lower={result.price_lower}
          upper={result.price_upper}
          perSqm={perSqm}
        />
      </div>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle className="text-xl text-primary">{t("detailsTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            <DetailRow
              label={t("location")}
              value={result.resolved_location.district || result.resolved_location.original}
              icon={<MapPin className="h-4 w-4" aria-hidden="true" />}
            />
            <DetailRow
              label={t("propertyType")}
              value={request.property_type}
              icon={<Building2 className="h-4 w-4" aria-hidden="true" />}
            />
            <DetailRow
              label={t("area")}
              value={`${formatNumber(request.area, locale)} m²`}
              icon={<Ruler className="h-4 w-4" aria-hidden="true" />}
            />
            <DetailRow
              label={t("beds")}
              value={String(request.beds)}
              icon={<BedDouble className="h-4 w-4" aria-hidden="true" />}
            />
            <DetailRow
              label={t("baths")}
              value={String(request.baths)}
              icon={<Bath className="h-4 w-4" aria-hidden="true" />}
            />
            <DetailRow
              label={t("furnishing")}
              value={request.furnishing}
              icon={<Sparkles className="h-4 w-4" aria-hidden="true" />}
            />
          </div>

          <Separator className="my-6" />

          <p className="text-xs leading-relaxed text-muted-foreground">
            {t("disclaimer")}
          </p>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <Button asChild variant="accent" size="lg" className="flex-1">
              <Link href="/recommendations">{t("viewSimilar")}</Link>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="lg"
              className="flex-1"
              onClick={() => router.push("/valuation")}
            >
              <RotateCcw className="h-4 w-4" aria-hidden="true" />
              {t("valueAnother")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}