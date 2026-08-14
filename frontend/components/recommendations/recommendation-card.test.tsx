import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { RecommendationCard } from "@/components/recommendations/recommendation-card";

const mockMessages = {
  "recommendations.card": {
    pricePerSqm: "/m²",
    beds: "beds",
    baths: "baths",
    comparable: "Comparable property",
    noImage: "No photo available",
  },
};

function mockTranslations(namespace: string) {
  const table = mockMessages[namespace as keyof typeof mockMessages];
  return (key: string) => table?.[key as keyof typeof table] ?? key;
}

const item = {
  price: 1_000_000,
  area: 150,
  beds: 2,
  baths: 2,
  property_type: "Apartment" as const,
  furnishing: "Unfurnished" as const,
  amenities: ["Pool"],
  location: "New Cairo",
  property_id: 1,
  similarity: 0.91,
};

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

describe("RecommendationCard", () => {
  it("shows a qualitative comparable label instead of a similarity percentage", () => {
    render(<RecommendationCard item={item} />);
    expect(screen.getByText("Comparable property")).toBeInTheDocument();
    expect(screen.queryByText(/91%/)).not.toBeInTheDocument();
    expect(screen.queryByText(/91 %/)).not.toBeInTheDocument();
  });

  it("shows the price without any match percentage", () => {
    render(<RecommendationCard item={item} />);
    expect(screen.getByText("EGP 1,000,000")).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it("links to the localized property route", () => {
    render(<RecommendationCard item={item} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/en/properties/1");
  });
});