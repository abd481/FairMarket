"use client";

import * as React from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useRouter } from "@/lib/navigation";
import { Loader2, MapPin, Ruler, BedDouble, Bath } from "lucide-react";

import {
  valuationFormSchema,
  emptyValuationValues,
  type ValuationFormValues,
} from "@/lib/validation";
import {
  AMENITIES,
  FURNISHING_OPTIONS,
  PROPERTY_TYPES,
  type PropertyType,
  type Furnishing,
} from "@/types/api";
import { usePredict } from "@/hooks/use-predict";
import { useValuationState } from "@/lib/valuation-store";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { LocationCombobox } from "./location-combobox";
import { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="text-xs text-destructive">{message}</p>;
}

export function ValuationForm() {
  const t = useTranslations("valuation");
  const tOptions = useTranslations("valuation.options");
  const router = useRouter();
  const predict = usePredict();
  const { setState } = useValuationState();

  const form = useForm<ValuationFormValues>({
    resolver: zodResolver(valuationFormSchema),
    defaultValues: emptyValuationValues,
  });

  const { register, handleSubmit, setValue, getValues, formState } =
    form;
  const { errors, isSubmitting } = formState;
  const watchedAmenities = useWatch({ control: form.control, name: "amenities" }) ?? [];
  const locationValue = useWatch({ control: form.control, name: "location" }) ?? "";
  const propertyTypeValue = useWatch({ control: form.control, name: "property_type" });
  const furnishingValue = useWatch({ control: form.control, name: "furnishing" });

  const onSubmit = handleSubmit(async (values) => {
    const result = await predict.mutateAsync(values);
    setState({ request: values, result });
    router.push("/result");
  });

  return (
    <Card className="mx-auto w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="text-2xl text-primary">{t("title")}</CardTitle>
        <CardDescription>{t("subtitle")}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} noValidate className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="location" className="flex items-center gap-1.5">
              <MapPin className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
              {t("fields.location")}
            </Label>
            <LocationCombobox
              value={locationValue}
              onChange={(value) => setValue("location", value, { shouldValidate: true })}
              hasError={!!errors.location}
            />
            <FieldError message={errors.location && t(`errors.${errors.location.message}`)} />
            <p className="text-xs text-muted-foreground">{t("fields.locationHint")}</p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="property_type">{t("fields.propertyType")}</Label>
              <Select
                value={propertyTypeValue}
                onValueChange={(v) =>
                  setValue("property_type", v as PropertyType, {
                    shouldValidate: true,
                  })
                }
              >
                <SelectTrigger id="property_type">
                  <SelectValue placeholder={t("placeholders.select")} />
                </SelectTrigger>
                <SelectContent>
                  {PROPERTY_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {tOptions(`propertyTypes.${type}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FieldError message={errors.property_type && t(`errors.${errors.property_type.message}`)} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="furnishing">{t("fields.furnishing")}</Label>
              <Select
                value={furnishingValue}
                onValueChange={(v) =>
                  setValue("furnishing", v as Furnishing, { shouldValidate: true })
                }
              >
                <SelectTrigger id="furnishing">
                  <SelectValue placeholder={t("placeholders.select")} />
                </SelectTrigger>
                <SelectContent>
                  {FURNISHING_OPTIONS.map((f) => (
                    <SelectItem key={f} value={f}>
                      {tOptions(`furnishing.${f}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FieldError message={errors.furnishing && t(`errors.${errors.furnishing.message}`)} />
            </div>
          </div>

          <div className="grid gap-6 sm:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="area" className="flex items-center gap-1.5">
                <Ruler className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                {t("fields.area")}
              </Label>
              <Input
                id="area"
                type="number"
                inputMode="decimal"
                min={1}
                step="any"
                placeholder={t("placeholders.area")}
                {...register("area")}
              />
              <FieldError message={errors.area && t(`errors.${errors.area.message}`)} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="beds" className="flex items-center gap-1.5">
                <BedDouble className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                {t("fields.beds")}
              </Label>
              <Input
                id="beds"
                type="number"
                inputMode="numeric"
                min={0}
                placeholder={t("placeholders.beds")}
                {...register("beds")}
              />
              <FieldError message={errors.beds && t(`errors.${errors.beds.message}`)} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="baths" className="flex items-center gap-1.5">
                <Bath className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                {t("fields.baths")}
              </Label>
              <Input
                id="baths"
                type="number"
                inputMode="numeric"
                min={1}
                placeholder={t("placeholders.baths")}
                {...register("baths")}
              />
              <FieldError message={errors.baths && t(`errors.${errors.baths.message}`)} />
            </div>
          </div>

          <div className="space-y-2">
            <Label>{t("fields.amenities")}</Label>
            <p className="text-xs text-muted-foreground">{t("fields.amenitiesHint")}</p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {AMENITIES.map((amenity) => {
                const checked = watchedAmenities.includes(amenity);
                return (
                  <label
                    key={amenity}
                    className={cn(
                      "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors",
                      checked
                        ? "border-accent bg-accent/10 text-foreground"
                        : "border-input bg-card text-muted-foreground hover:bg-secondary",
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        const current = getValues("amenities");
                        const next = e.target.checked
                          ? [...current, amenity]
                          : current.filter((a) => a !== amenity);
                        setValue("amenities", next, { shouldValidate: true });
                      }}
                      className="sr-only"
                    />
                    {tOptions(`amenities.${amenity}`)}
                  </label>
                );
              })}
            </div>
          </div>

          {predict.isError && (
            <div
              role="alert"
              className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
            >
              {predict.error instanceof ApiError && predict.error.status === 400
                ? t("locationNotFound")
                : t("apiError")}
            </div>
          )}

          <Button
            type="submit"
            variant="accent"
            size="lg"
            className="w-full"
            disabled={isSubmitting || predict.isPending}
          >
            {isSubmitting || predict.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                {t("submitting")}
              </>
            ) : (
              t("submit")
            )}
          </Button>
          {predict.isPending && (
            <p className="text-center text-sm text-muted-foreground">
              {t("submittingHint")}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  );
}