import { setRequestLocale } from "next-intl/server";
import { RecommendationsView } from "@/components/recommendations/recommendations-view";

export default async function RecommendationsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  return <RecommendationsView />;
}