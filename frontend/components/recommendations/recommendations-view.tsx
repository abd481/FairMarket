"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import {
  SearchX,
  AlertTriangle,
  RotateCcw,
  ArrowLeft,
} from "lucide-react";
import { Link } from "@/lib/navigation";
import {
  useValuationState,
  sortRecommendations,
} from "@/lib/valuation-store";
import { useRecommend } from "@/hooks/use-predict";
import { PROPERTY_TYPES } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  RecommendationCard,
  RecommendationCardSkeleton,
} from "./recommendation-card";

export function RecommendationsView() {
  const t = useTranslations("recommendations");
  const tOptions = useTranslations("valuation.options");
  const { state } = useValuationState();
  const recommend = useRecommend();

  const [priceMin, setPriceMin] = React.useState<string>("");
  const [priceMax, setPriceMax] = React.useState<string>("");
  const [location, setLocation] = React.useState<string>("all");
  const [propertyType, setPropertyType] = React.useState<string>("all");

  React.useEffect(() => {
    if (state && !recommend.isSuccess && !recommend.isPending) {
      recommend.mutate(state.request);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state?.request]);

  const locations = React.useMemo(() => {
    if (!recommend.data) return [];
    return Array.from(
      new Set(recommend.data.recommendations.map((r) => r.location)),
    ).sort();
  }, [recommend.data]);

  const filtered = React.useMemo(() => {
    if (!recommend.data) return [];
    const min = priceMin === "" ? null : Number(priceMin);
    const max = priceMax === "" ? null : Number(priceMax);
    return sortRecommendations(
      recommend.data.recommendations.filter((r) => {
        if (location !== "all" && r.location !== location) return false;
        if (propertyType !== "all" && r.property_type !== propertyType) return false;
        if (min !== null && !Number.isNaN(min) && r.price < min) return false;
        if (max !== null && !Number.isNaN(max) && r.price > max) return false;
        return true;
      }),
    );
  }, [recommend.data, priceMin, priceMax, location, propertyType]);

  const clearFilters = React.useCallback(() => {
    setPriceMin("");
    setPriceMax("");
    setLocation("all");
    setPropertyType("all");
  }, []);

  const hasActiveFilters =
    priceMin !== "" || priceMax !== "" || location !== "all" || propertyType !== "all";

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-primary">
            {t("title")}
          </h1>
          <p className="mt-2 text-muted-foreground">{t("subtitle")}</p>
          <p className="mt-1 text-xs text-muted-foreground/80">{t("rankNote")}</p>
        </div>
        <div className="flex gap-2">
          {state && (
            <Button asChild variant="outline" size="sm">
              <Link href="/result">
                <ArrowLeft className="h-4 w-4 rtl:rotate-180" aria-hidden="true" />
                {t("backToResult")}
              </Link>
            </Button>
          )}
          <Button asChild variant="ghost" size="sm">
            <Link href="/valuation">{t("backToValuation")}</Link>
          </Button>
        </div>
      </div>

      <div className="mt-8 rounded-xl border bg-card p-5 shadow-sm">
        <p className="mb-4 text-sm font-semibold text-foreground">
          {t("filters.title")}
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-2">
            <Label htmlFor="price-min">{t("filters.priceMin")}</Label>
            <Input
              id="price-min"
              type="number"
              inputMode="numeric"
              min={0}
              value={priceMin}
              onChange={(e) => setPriceMin(e.target.value)}
              placeholder="0"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="price-max">{t("filters.priceMax")}</Label>
            <Input
              id="price-max"
              type="number"
              inputMode="numeric"
              min={0}
              value={priceMax}
              onChange={(e) => setPriceMax(e.target.value)}
              placeholder="∞"
            />
          </div>
          <div className="space-y-2">
            <Label>{t("filters.location")}</Label>
            <Select value={location} onValueChange={setLocation}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("filters.clear")}</SelectItem>
                {locations.map((loc) => (
                  <SelectItem key={loc} value={loc}>
                    {loc}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>{t("filters.propertyType")}</Label>
            <Select value={propertyType} onValueChange={setPropertyType}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("filters.clear")}</SelectItem>
                {PROPERTY_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {tOptions(`propertyTypes.${type}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" className="mt-4" onClick={clearFilters}>
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            {t("filters.clear")}
          </Button>
        )}
      </div>

      <div className="mt-8">
        {recommend.isPending && (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <RecommendationCardSkeleton key={i} />
            ))}
          </div>
        )}

        {recommend.isError && (
          <div className="flex flex-col items-center rounded-xl border border-destructive/30 bg-destructive/10 px-6 py-16 text-center">
            <AlertTriangle className="h-10 w-10 text-destructive" aria-hidden="true" />
            <h2 className="mt-4 text-xl font-semibold text-foreground">
              {t("errorTitle")}
            </h2>
            <p className="mt-2 text-muted-foreground">{t("errorDescription")}</p>
          </div>
        )}

        {recommend.isSuccess && filtered.length === 0 && (
          <div className="flex flex-col items-center rounded-xl border bg-card px-6 py-16 text-center shadow-sm">
            <SearchX className="h-10 w-10 text-muted-foreground" aria-hidden="true" />
            <h2 className="mt-4 text-xl font-semibold text-foreground">
              {t("emptyTitle")}
            </h2>
            <p className="mt-2 text-muted-foreground">{t("emptyDescription")}</p>
            <Button variant="outline" className="mt-6" onClick={clearFilters}>
              {t("filters.clear")}
            </Button>
          </div>
        )}

        {recommend.isSuccess && filtered.length > 0 && (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((item) => (
              <RecommendationCard key={item.property_id} item={item} />
            ))}
          </div>
        )}

        {recommend.isSuccess && filtered.length > 0 && (
          <p className="mt-8 text-center text-sm text-muted-foreground">
            {filtered.length}{" "}
            {t("subtitle")}
          </p>
        )}
      </div>
    </div>
  );
}