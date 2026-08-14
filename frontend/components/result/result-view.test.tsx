import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import { ResultView } from "@/components/result/result-view";

const mockMessages = {
  result: {
    badge: "Data-powered estimate",
    predictedLabel: "Estimated fair price",
    rangeLabel: "Estimated fair price range",
    pricePerSqm: "Price per m²",
    detailsTitle: "Property details",
    location: "Location",
    propertyType: "Property type",
    area: "Area",
    beds: "Bedrooms",
    baths: "Bathrooms",
    furnishing: "Furnishing",
    disclaimer: "Disclaimer text",
    viewSimilar: "View similar properties",
    valueAnother: "Value another property",
    emptyTitle: "No estimate yet",
    emptyDescription: "Value a property first",
    title: "Fair price valuation",
  },
};

function mockTranslations(namespace: string) {
  const table = mockMessages[namespace as keyof typeof mockMessages];
  return (key: string) => table?.[key as keyof typeof table] ?? key;
}

const state = {
  request: {
    area: 150,
    beds: 2,
    baths: 2,
    property_type: "Apartment",
    furnishing: "Unfurnished",
  },
  result: {
    predicted_price: 1_000_000,
    price_lower: 900_000,
    price_upper: 1_100_000,
    resolved_location: {
      original: "New Cairo",
      district: "New Cairo",
      matched: true,
    },
  },
};

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => mockTranslations(namespace),
  useLocale: () => "en",
}));

vi.mock("@/lib/navigation", () => ({
  Link: ({ children }: { children: React.ReactNode }) => <a>{children}</a>,
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/lib/valuation-store", () => ({
  useValuationState: () => ({ state }),
}));

describe("ResultView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows the estimated fair price as the primary value", () => {
    render(<ResultView />);
    expect(screen.getByText("Estimated fair price")).toBeInTheDocument();
    expect(screen.getByText("EGP 1,000,000")).toBeInTheDocument();
  });

  it("shows the fair price range below the estimate", () => {
    render(<ResultView />);
    expect(screen.getByText("Estimated fair price range")).toBeInTheDocument();
    expect(screen.getByText("EGP 900,000")).toBeInTheDocument();
    expect(screen.getByText("EGP 1,100,000")).toBeInTheDocument();
  });

  it("shows the price per m²", () => {
    render(<ResultView />);
    expect(screen.getByText(/Price per m²/)).toBeInTheDocument();
    expect(screen.getByText("EGP 6,667")).toBeInTheDocument();
  });
});
