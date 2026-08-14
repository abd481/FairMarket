import { setRequestLocale } from "next-intl/server";
import { ResultView } from "@/components/result/result-view";

export default async function ResultPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  return <ResultView />;
}