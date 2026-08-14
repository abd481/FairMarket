import { setRequestLocale } from "next-intl/server";
import { Hero, TrustSection, HowItWorks, FinalCta } from "@/components/landing/sections";

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <>
      <Hero />
      <TrustSection />
      <HowItWorks />
      <FinalCta />
    </>
  );
}