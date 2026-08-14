# FairMarket Frontend

The FairMarket web app — an AI-powered platform that estimates fair property prices in Egypt. This Next.js app talks to the FastAPI backend in the repository root.

## Tech stack

- Next.js 16 (App Router) + TypeScript
- Tailwind CSS v4 with a custom design system
- shadcn/ui-style components (`components/ui/`)
- React Hook Form + Zod for form validation
- TanStack Query for server state
- next-intl for English + Egyptian Arabic (RTL) i18n
- lucide-react for icons

## Getting started

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Configure the API

Create `.env.local` with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The app expects the FastAPI backend (root of this repo) to be running on port 8000. Start it with:

```bash
poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000
```

> **CORS:** The backend reads `CORS_ORIGINS` from its `.env` file. Add the frontend origin there, e.g. `CORS_ORIGINS = 'http://localhost:3000'`, otherwise the browser will block requests.

## Scripts

| Command          | Description                                    |
| ---------------- | ---------------------------------------------- |
| `npm run dev`    | Start the dev server                           |
| `npm run build`  | Production build (type-checked, linted)        |
| `npm run start`  | Serve the production build                     |
| `npm run lint`   | Run ESLint                                     |
| `npm test`       | Run the Vitest suite                           |

## Project structure

```
frontend/
  app/                 # App Router pages ([locale]/ + valuation, result, recommendations)
  components/
    ui/                # Design-system primitives (Button, Card, Input, Select, Badge, …)
    layout/            # Header, footer, language switcher, logo
    valuation/         # Valuation form + location combobox
    result/            # Estimate result view
    recommendations/   # Recommendation cards, filters, skeletons
    landing/           # Home page sections
  hooks/               # TanStack Query hooks (locations, predict, recommend, health)
  lib/                 # api client, validation schemas, utils, navigation, store
  messages/            # en.json + ar.json (Egyptian Arabic)
  types/               # TS types mirroring api/schemas.py
  i18n/                # next-intl routing + request config
  proxy.ts             # Locale handling (Next 16 proxy)
```

## API contract

The frontend's TypeScript types in `types/api.ts` mirror the Pydantic schemas in `api/schemas.py`. The centralized client lives in `lib/api.ts`. Endpoints used:

- `GET /api/locations` — known locations (drives the searchable dropdown)
- `POST /api/predict` — price estimate for a property
- `POST /api/recommend` — comparable listings
- `GET /health` — service health

## Deployment (Vercel)

1. Push this repository (the `frontend/` folder is the app root).
2. In Vercel: **Import Project** → set **Root Directory** to `frontend`.
3. Add the environment variable:
   - `NEXT_PUBLIC_API_URL` → your deployed API base URL (must be HTTPS in production)
4. Deploy. Vercel runs `npm run build` automatically.

The Arabic locale (`/ar`) and RTL are supported out of the box — no extra configuration needed on Vercel.

## i18n

- Add or edit strings in `messages/en.json` (English) and `messages/ar.json` (Egyptian Arabic).
- The locale is negotiated by `proxy.ts` (Next 16 proxy convention) and persisted.
- Use `useTranslations("namespace")` in client components and `getTranslations` in server components.

## Notes

- No Redux — server state is TanStack Query; page-to-page flow data lives in a small session-backed store (`lib/valuation-store.ts`).
- Keep `types/api.ts` in sync with `api/schemas.py` whenever the backend contract changes.
