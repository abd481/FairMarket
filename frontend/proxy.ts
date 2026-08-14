import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  // Skip API routes and Next.js internals; only localize public pages.
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};