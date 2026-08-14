import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import { getMessages } from "next-intl/server";

import { routing } from "@/i18n/routing";
import { geistSans, geistMono, cairo } from "@/lib/fonts";
import { QueryProvider } from "@/components/providers/query-provider";
import { SiteHeader } from "@/components/layout/site-header";
import { SiteFooter } from "@/components/layout/site-footer";
import "../globals.css";

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const isAr = locale === "ar";
  return {
    title: isAr
      ? "FairMarket — اعرف السعر العادل لعقارك في مصر"
      : "FairMarket — Know the fair value of your property in Egypt",
    description: isAr
      ? "تقدير أسعار العقارات بالذكاء الاصطناعي في مصر من بيانات السوق الحقيقية."
      : "AI-powered property valuation in Egypt from real market data.",
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!routing.locales.includes(locale as (typeof routing.locales)[number])) {
    notFound();
  }

  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <html
      lang={locale}
      dir={locale === "ar" ? "rtl" : "ltr"}
      data-scroll-behavior="smooth"
      className={`${geistSans.variable} ${geistMono.variable} ${cairo.variable} h-full`}
    >
      <body className="min-h-full flex flex-col">
        <QueryProvider>
          <NextIntlClientProvider messages={messages}>
            <SiteHeader />
            <main className="flex-1">{children}</main>
            <SiteFooter />
          </NextIntlClientProvider>
        </QueryProvider>
      </body>
    </html>
  );
}