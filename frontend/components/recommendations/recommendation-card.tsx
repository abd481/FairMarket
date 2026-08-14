"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useLocale } from "next-intl";
import { Building2, BedDouble, Bath, Ruler, MapPin } from "lucide-react";

import { formatEGP, formatNumber, formatPricePerSqm } from "@/lib/utils";
import type { Recommendation } from "@/types/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Link } from "@/lib/navigation";

function PropertyImage({ type, location }: { type: string; location: string }) {
  return (
    <div
      className="relative flex h-44 w-full items-center justify-center overflow-hidden bg-gradient-to-br from-primary/15 to-accent/10"
      aria-hidden="true"
    >
      <Building2 className="h-14 w-14 text-primary/30" />
      <div className="absolute bottom-2 start-2">
        <Badge variant="gold" className="backdrop-blur">
          {type}
        </Badge>
      </div>
      <span className="sr-only">{`${type} ${location}`}</span>
    </div>
  );
}

export function RecommendationCard({ item }: { item: Recommendation }) {
  const locale = useLocale();
  const t = useTranslations("recommendations.card");

  return (
    <Link
      href={`/properties/${item.property_id}`}
      aria-label={`${item.property_type} ${item.location}`}
      className="group block h-full rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
    >
      <Card className="h-full overflow-hidden transition-shadow group-hover:shadow-md">
        <PropertyImage type={item.property_type} location={item.location} />
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-2">
            <p className="text-lg font-bold text-primary">
              {formatEGP(item.price, locale)}
            </p>
            <Badge variant="accent" className="shrink-0">
              {t("comparable")}
            </Badge>
          </div>
          <p className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
            <MapPin className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span className="truncate">{item.location}</span>
          </p>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <BedDouble className="h-3.5 w-3.5" aria-hidden="true" />
              {item.beds} {t("beds")}
            </span>
            <span className="flex items-center gap-1">
              <Bath className="h-3.5 w-3.5" aria-hidden="true" />
              {item.baths} {t("baths")}
            </span>
            <span className="flex items-center gap-1">
              <Ruler className="h-3.5 w-3.5" aria-hidden="true" />
              {formatNumber(item.area, locale)} m²
            </span>
          </div>
          <p className="mt-3 border-t pt-2 text-xs text-muted-foreground">
            {formatPricePerSqm(item.price, item.area, locale)}
            <span className="ms-1">{t("pricePerSqm")}</span>
          </p>
        </CardContent>
      </Card>
    </Link>
  );
}

export function RecommendationCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <div className="h-44 w-full animate-pulse bg-secondary" />
      <CardContent className="space-y-3 p-4">
        <div className="h-5 w-1/2 animate-pulse rounded bg-secondary" />
        <div className="h-4 w-3/4 animate-pulse rounded bg-secondary" />
        <div className="h-4 w-2/3 animate-pulse rounded bg-secondary" />
      </CardContent>
    </Card>
  );
}