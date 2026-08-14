"use client";

import * as React from "react";
import { useTranslations, useLocale } from "next-intl";
import {
  MapPin,
  Ruler,
  BedDouble,
  Bath,
  Sparkles,
  Building2,
  ExternalLink,
  ArrowRight,
  ArrowLeft,
  SearchX,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";

import { Link } from "@/lib/navigation";
import { ApiError } from "@/lib/api";
import { useProperty } from "@/hooks/use-property";
import { formatEGP, formatNumber, formatPricePerSqm } from "@/lib/utils";
import type { PropertyDetail } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";

function isValidExternalUrl(value?: string | null): boolean {
  if (!value) return false;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function PropertyDetailSkeleton() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 sm:py-16">
      <Skeleton className="h-9 w-48" />
      <Card className="mt-6">
        <CardContent className="p-6 sm:p-8">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="mt-4 h-9 w-2/3" />
          <Skeleton className="mt-3 h-5 w-1/2" />
          <Skeleton className="mt-6 h-12 w-40" />
          <Separator className="my-6" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
          <Skeleton className="mt-6 h-8 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}

function DetailRow({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
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

function BackToSimilar({ t }: { t: (key: string) => string }) {
  const locale = useLocale();
  const ArrowIcon = locale === "ar" ? ArrowRight : ArrowLeft;
  return (
    <Button asChild variant="ghost" size="sm" className="px-0">
      <Link href="/recommendations">
        <ArrowIcon className="h-4 w-4 rtl:rotate-180" aria-hidden="true" />
        {t("backToSimilar")}
      </Link>
    </Button>
  );
}

function PropertyDetails({ property }: { property: PropertyDetail }) {
  const t = useTranslations("property");
  const locale = useLocale();
  const ArrowIcon = locale === "ar" ? ArrowLeft : ArrowRight;

  const title = property.title?.trim() || t("fallbackTitle");
  const location =
    property.district ||
    property.city ||
    property.compound ||
    property.location;
  const perSqm = formatPricePerSqm(
    property.price,
    property.area,
    locale,
  );
  const externalLink = isValidExternalUrl(property.link) ? property.link : null;

  return (
    <Card className="mt-6 overflow-hidden">
      <CardContent className="p-6 sm:p-8">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="accent">{t("propertyType")}</Badge>
          <Badge variant="gold">{property.property_type}</Badge>
          {property.source && (
            <Badge variant="secondary" className="capitalize">
              {property.source}
            </Badge>
          )}
        </div>

        <h1 className="mt-4 text-3xl font-bold tracking-tight text-primary">
          {title}
        </h1>

        <p className="mt-2 flex items-center gap-1 text-muted-foreground">
          <MapPin className="h-4 w-4" aria-hidden="true" />
          <span>{location}</span>
        </p>

        <p className="mt-6 text-4xl font-bold tracking-tight text-primary sm:text-5xl">
          {formatEGP(property.price, locale)}
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("pricePerSqm")}: {perSqm}
        </p>

        <Separator className="my-6" />

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <DetailRow
            label={t("area")}
            value={`${formatNumber(property.area, locale)} m²`}
            icon={<Ruler className="h-4 w-4" aria-hidden="true" />}
          />
          <DetailRow
            label={t("beds")}
            value={String(property.beds)}
            icon={<BedDouble className="h-4 w-4" aria-hidden="true" />}
          />
          <DetailRow
            label={t("baths")}
            value={String(property.baths)}
            icon={<Bath className="h-4 w-4" aria-hidden="true" />}
          />
          <DetailRow
            label={t("furnishing")}
            value={
              property.furnishing
                ? t(
                    property.furnishing === "Furnished"
                      ? "furnished"
                      : property.furnishing === "Unfurnished"
                        ? "unfurnished"
                        : "notSpecified",
                  )
                : t("notSpecified")
            }
            icon={<Sparkles className="h-4 w-4" aria-hidden="true" />}
          />
          <DetailRow
            label={t("location")}
            value={property.location}
            icon={<MapPin className="h-4 w-4" aria-hidden="true" />}
          />
          <DetailRow
            label={t("propertyType")}
            value={property.property_type}
            icon={<Building2 className="h-4 w-4" aria-hidden="true" />}
          />
        </div>

        {property.amenities.length > 0 && (
          <>
            <Separator className="my-6" />
            <p className="text-sm font-medium text-foreground">{t("amenities")}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {property.amenities.map((amenity) => (
                <Badge key={amenity} variant="outline">
                  {amenity}
                </Badge>
              ))}
            </div>
          </>
        )}

        <Separator className="my-6" />

        <div className="flex flex-col gap-3 sm:flex-row">
          {externalLink ? (
            <Button asChild variant="accent" size="lg" className="flex-1">
              <a href={externalLink} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4" aria-hidden="true" />
                {t("viewListing")}
              </a>
            </Button>
          ) : (
            <div className="flex-1" />
          )}
          <Button asChild variant="outline" size="lg" className="flex-1">
            <Link href="/recommendations">
              <ArrowIcon className="h-4 w-4 rtl:rotate-180" aria-hidden="true" />
              {t("backToSimilar")}
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function PropertyDetailView({ propertyId }: { propertyId: string }) {
  const t = useTranslations("property");
  const query = useProperty(Number(propertyId));

  const id = Number(propertyId);
  const invalidId = !Number.isInteger(id) || id <= 0;

  if (invalidId) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center px-4 py-20 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-secondary">
          <SearchX className="h-7 w-7 text-primary" aria-hidden="true" />
        </div>
        <h1 className="mt-6 text-2xl font-bold text-primary">
          {t("notFoundTitle")}
        </h1>
        <p className="mt-2 text-muted-foreground">{t("notFoundDescription")}</p>
        <div className="mt-8">
          <BackToSimilar t={t} />
        </div>
      </div>
    );
  }

  if (query.isPending || query.isLoading) {
    return <PropertyDetailSkeleton />;
  }

  if (query.isError) {
    const status = query.error instanceof ApiError ? query.error.status : null;
    if (status === 404) {
      return (
        <div className="mx-auto flex max-w-md flex-col items-center px-4 py-20 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-secondary">
            <SearchX className="h-7 w-7 text-primary" aria-hidden="true" />
          </div>
          <h1 className="mt-6 text-2xl font-bold text-primary">
            {t("notFoundTitle")}
          </h1>
          <p className="mt-2 text-muted-foreground">{t("notFoundDescription")}</p>
          <div className="mt-8">
            <BackToSimilar t={t} />
          </div>
        </div>
      );
    }

    return (
      <div className="mx-auto flex max-w-md flex-col items-center px-4 py-20 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10">
          <AlertTriangle
            className="h-7 w-7 text-destructive"
            aria-hidden="true"
          />
        </div>
        <h1 className="mt-6 text-2xl font-bold text-primary">
          {t("errorTitle")}
        </h1>
        <p className="mt-2 text-muted-foreground">{t("errorDescription")}</p>
        <Button variant="outline" className="mt-8" onClick={() => query.refetch()}>
          <RotateCcw className="h-4 w-4" aria-hidden="true" />
          {t("retry")}
        </Button>
      </div>
    );
  }

  if (!query.data) {
    return <PropertyDetailSkeleton />;
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 sm:py-16">
      <BackToSimilar t={t} />
      <PropertyDetails property={query.data} />
    </div>
  );
}