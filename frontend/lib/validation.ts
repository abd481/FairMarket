import { z } from "zod";
import { FURNISHING_OPTIONS, PROPERTY_TYPES } from "@/types/api";

export const valuationFormSchema = z.object({
  location: z
    .string()
    .min(1, "locationRequired"),
  property_type: z.enum(PROPERTY_TYPES, {
    errorMap: () => ({ message: "required" }),
  }),
  area: z.coerce
    .number({ invalid_type_error: "areaNumber" })
    .positive("areaMin"),
  beds: z.coerce.number({ invalid_type_error: "bedsNumber" }).int().min(0, "bedsNumber"),
  baths: z.coerce.number({ invalid_type_error: "bathsNumber" }).int().min(1, "bathsMin"),
  furnishing: z.enum(FURNISHING_OPTIONS, {
    errorMap: () => ({ message: "required" }),
  }),
  amenities: z.array(z.string()),
});

export type ValuationFormValues = z.infer<typeof valuationFormSchema>;

export const emptyValuationValues: ValuationFormValues = {
  location: "",
  property_type: "Apartment",
  area: 0,
  beds: 0,
  baths: 1,
  furnishing: "Unfurnished",
  amenities: [],
};