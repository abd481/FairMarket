import { describe, it, expect } from "vitest";
import {
  valuationFormSchema,
  emptyValuationValues,
} from "@/lib/validation";

const validBase = {
  location: "New Cairo",
  property_type: "Apartment",
  area: 150,
  beds: 3,
  baths: 2,
  furnishing: "Unfurnished",
  amenities: [],
} as const;

describe("valuationFormSchema", () => {
  it("accepts a valid submission", () => {
    const result = valuationFormSchema.safeParse(validBase);
    expect(result.success).toBe(true);
  });

  it("requires a location", () => {
    const result = valuationFormSchema.safeParse({ ...validBase, location: "" });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("locationRequired");
    }
  });

  it("requires area to be positive", () => {
    const result = valuationFormSchema.safeParse({ ...validBase, area: 0 });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("areaMin");
    }
  });

  it("requires baths to be at least 1", () => {
    const result = valuationFormSchema.safeParse({ ...validBase, baths: 0 });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("bathsMin");
    }
  });

  it("accepts beds = 0", () => {
    const result = valuationFormSchema.safeParse({ ...validBase, beds: 0 });
    expect(result.success).toBe(true);
  });

  it("coerces numeric strings", () => {
    const result = valuationFormSchema.safeParse({
      ...validBase,
      area: "150",
      beds: "3",
      baths: "2",
    });
    expect(result.success).toBe(true);
  });

  it("rejects invalid property types", () => {
    const result = valuationFormSchema.safeParse({
      ...validBase,
      property_type: "Cottage",
    });
    expect(result.success).toBe(false);
  });

  it("rejects negative beds", () => {
    const result = valuationFormSchema.safeParse({ ...validBase, beds: -1 });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("bedsNumber");
    }
  });
});

describe("emptyValuationValues", () => {
  it("starts with area 0 (invalid until the user fills it)", () => {
    expect(emptyValuationValues.area).toBe(0);
    const result = valuationFormSchema.safeParse(emptyValuationValues);
    expect(result.success).toBe(false);
  });
});