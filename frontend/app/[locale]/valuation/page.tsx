import { setRequestLocale } from "next-intl/server";
import { ValuationForm } from "@/components/valuation/valuation-form";

export default async function ValuationPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
      <ValuationForm />
    </div>
  );
}