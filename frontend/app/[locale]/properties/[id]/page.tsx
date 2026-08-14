import { setRequestLocale } from "next-intl/server";
import { PropertyDetailView } from "@/components/properties/property-detail-view";

export default async function PropertyDetailPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);

  return <PropertyDetailView propertyId={id} />;
}