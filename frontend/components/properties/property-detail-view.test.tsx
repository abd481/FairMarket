import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { PropertyDetailView } from "@/components/properties/property-detail-view";
import { ApiError } from "@/lib/api";
import type { PropertyDetail } from "@/types/api";

const mockMessages = {
  property: {
    fallbackTitle: "Property listing",
    propertyType: "Property type",
    pricePerSqm: "Price per m²",
    location: "Location",
    area: "Area",
    beds: "Bedrooms",
    baths: "Bathrooms",
    furnishing: "Furnishing",
    amenities: "Amenities",
    furnished: "Furnished",
    unfurnished: "Unfurnished",
    notSpecified: "Not specified",
    viewListing: "View original listing",
    backToSimilar: "Back to similar properties",
    loading: "Loading property details…",
    errorTitle: "We couldn't load this property",
    errorDescription: "Please try again in a moment.",
    retry: "Try again",
    notFoundTitle: "Property not found",
    notFoundDescription: "This listing may no longer be available.",
  },
};

function mockTranslations(namespace: string) {
  const table = mockMessages[namespace as keyof typeof mockMessages];
  return (key: string) => table?.[key as keyof typeof table] ?? key;
}

const property: PropertyDetail = {
  id: 123,
  title: "Luxury 3BR in Crescent Walk",
  price: 5_500_000,
  area: 160,
  beds: 3,
  baths: 2,
  location: "Crescent Walk, 6th Settlement",
  district: "6th Settlement",
  city: "New Cairo",
  compound: "Crescent Walk",
  property_type: "Apartment",
  furnishing: "Furnished",
  amenities: ["Pool", "Security", "Balcony"],
  price_per_sqm: 34_375,
  source: "bayut",
  link: "https://bayut.example.com/listing/123",
};

let mockPropertyResult: unknown;

vi.mock("@/hooks/use-property", () => ({
  useProperty: () => mockPropertyResult,
}));

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => mockTranslations(namespace),
  useLocale: () => "en",
}));

vi.mock("@/lib/navigation", () => ({
  Link: ({
    href,
    children,
    ...props
  }: {
    href: string;
    children: React.ReactNode;
  }) => (
    <a href={`/en${href}`} {...props}>
      {children}
    </a>
  ),
}));

describe("PropertyDetailView", () => {
  it("renders property data", () => {
    mockPropertyResult = {
      data: property,
      isPending: false,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    };
    render(<PropertyDetailView propertyId="123" />);

    expect(
      screen.getByRole("heading", { name: "Luxury 3BR in Crescent Walk" }),
    ).toBeInTheDocument();
    expect(screen.getByText("EGP 5,500,000")).toBeInTheDocument();
    expect(screen.getByText("Crescent Walk, 6th Settlement")).toBeInTheDocument();
    expect(screen.getByText("160 m²")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("Furnished")).toBeInTheDocument();
    expect(screen.getByText("Pool")).toBeInTheDocument();
    expect(screen.getByText("bayut")).toBeInTheDocument();
  });

  it("shows a localized fallback title when title is absent", () => {
    mockPropertyResult = {
      data: { ...property, title: null },
      isPending: false,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    };
    render(<PropertyDetailView propertyId="123" />);
    expect(
      screen.getByRole("heading", { name: "Property listing" }),
    ).toBeInTheDocument();
  });

  it("shows the localized not-found state on 404", () => {
    mockPropertyResult = {
      data: undefined,
      isPending: false,
      isLoading: false,
      isError: true,
      error: new ApiError("not found", 404, "Property not found."),
      refetch: vi.fn(),
    };
    render(<PropertyDetailView propertyId="999" />);
    expect(
      screen.getByRole("heading", { name: "Property not found" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("This listing may no longer be available."),
    ).toBeInTheDocument();
  });

  it("renders a safe external listing link", () => {
    mockPropertyResult = {
      data: property,
      isPending: false,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    };
    render(<PropertyDetailView propertyId="123" />);

    const external = screen.getByRole("link", {
      name: "View original listing",
    });
    expect(external).toHaveAttribute(
      "href",
      "https://bayut.example.com/listing/123",
    );
    expect(external).toHaveAttribute("target", "_blank");
    expect(external).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("omits the external listing link for invalid URLs", () => {
    mockPropertyResult = {
      data: { ...property, link: "javascript:alert(1)" },
      isPending: false,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    };
    render(<PropertyDetailView propertyId="123" />);
    expect(
      screen.queryByRole("link", { name: "View original listing" }),
    ).not.toBeInTheDocument();
  });

  it("shows the localized not-found state for an invalid id", () => {
    mockPropertyResult = {
      data: undefined,
      isPending: true,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    };
    render(<PropertyDetailView propertyId="not-a-number" />);
    expect(
      screen.getByRole("heading", { name: "Property not found" }),
    ).toBeInTheDocument();
  });
});