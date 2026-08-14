import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { ApiError, api } from "@/lib/api";
import type { PredictRequest } from "@/types/api";

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  mockFetch.mockReset();
});

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api.getLocations", () => {
  it("returns the locations array", async () => {
    mockFetch.mockResolvedValue(jsonResponse(["New Cairo", "Sheikh Zayed"]));
    const result = await api.getLocations();
    expect(result).toEqual(["New Cairo", "Sheikh Zayed"]);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/locations"),
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("throws ApiError with detail on non-ok response", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ error: "boom", detail: "Upstream failed" }, 500),
    );
    await expect(api.getLocations()).rejects.toMatchObject({
      name: "ApiError",
      status: 500,
      detail: "Upstream failed",
    });
  });

  it("throws a network ApiError when fetch rejects", async () => {
    mockFetch.mockRejectedValue(new TypeError("fetch failed"));
    await expect(api.getLocations()).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });
  });
});

describe("api.predict", () => {
  it("posts the request body as JSON", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({
        predicted_price: 4000000,
        price_upper: 4400000,
        price_lower: 3600000,
        resolved_location: {
          original: "New Cairo",
          district: "New Cairo",
          city: "Cairo",
          matched: true,
        },
      }),
    );

    const body: PredictRequest = {
      area: 150,
      beds: 3,
      baths: 2,
      location: "New Cairo",
      property_type: "Apartment",
      furnishing: "Unfurnished",
      amenities: ["pool"],
    };

    const result = await api.predict(body);
    expect(result.predicted_price).toBe(4000000);

    const [, init] = mockFetch.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual(body);
  });
});

describe("api.recommend", () => {
  it("returns recommendations and resolves types", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({
        filtered_by: "features_only",
        recommendations: [
          {
            price: 3800000,
            beds: 3,
            baths: 2,
            area: 140,
            location: "New Cairo",
            property_type: "Apartment",
            furnishing: null,
            amenities: ["pool"],
            property_id: 12,
            similarity: 0.93,
          },
        ],
        predicted_fair_price: 4000000,
        resolved_location: {
          original: "New Cairo",
          district: "New Cairo",
          city: "Cairo",
          matched: true,
        },
      }),
    );

    const result = await api.recommend({
      area: 150,
      beds: 3,
      baths: 2,
      location: "New Cairo",
      property_type: "Apartment",
      furnishing: "Unfurnished",
      amenities: [],
    });

    expect(result.recommendations[0].property_id).toBe(12);
    expect(result.recommendations[0].similarity).toBeCloseTo(0.93);
  });
});

describe("api.getProperty", () => {
  it("fetches a property by id", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({
        id: 123,
        title: "Luxury 3BR",
        price: 5500000,
        area: 160,
        beds: 3,
        baths: 2,
        location: "Crescent Walk, 6th Settlement",
        property_type: "Apartment",
        furnishing: "Furnished",
        amenities: ["Pool"],
        price_per_sqm: 34375,
        source: "bayut",
        link: "https://example.com/1",
      }),
    );

    const result = await api.getProperty(123);
    expect(result.id).toBe(123);
    expect(result.price).toBe(5500000);
    expect(result.amenities).toEqual(["Pool"]);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/properties/123"),
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("surfaces a 404 as an ApiError", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ detail: "not found" }, 404));
    await expect(api.getProperty(999)).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
    });
  });
});

describe("ApiError", () => {
  it("is an Error with status/detail", () => {
    const err = new ApiError("message", 422, "detail", "code");
    expect(err).toBeInstanceOf(Error);
    expect(err.status).toBe(422);
    expect(err.detail).toBe("detail");
    expect(err.code).toBe("code");
  });
});