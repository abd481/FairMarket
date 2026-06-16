# Real Estate Pipeline

[![CI](https://github.com/abd481/Real-estate-end-to-end-System-/actions/workflows/ci.yml/badge.svg)](https://github.com/abd481/Real-estate-end-to-end-System-/actions/workflows/ci.yml)

An end-to-end real estate data pipeline for the Egyptian market. It scrapes property listings, validates and cleans them, engineers features, and stores ready-to-use datasets for downstream analysis and machine learning.

The project is built to be practical rather than flashy: it focuses on getting reliable property data into a shape that is easy to inspect, test, and reuse.

## What it does

- Scrapes listings from configured sources such as Bayut and OLX.
- Validates incoming records before they reach the database.
- Cleans and normalizes property fields like price, beds, baths, amenities, and location.
- Preprocesses the cleaned dataset into train, validation, and test splits.
- Persists the preprocessing pipeline as a reusable `joblib` artifact.
- Sends Telegram notifications when the pipeline succeeds or fails.

## Project Layout

- `scrapers/` contains source-specific scraping logic and JSON configs.
- `data/ingestion/` handles database insertion and record logging.
- `data/processing/` contains cleaning, normalization, transformation, and preprocessing steps.
- `data/validation/` defines schema and rule checks for listings.
- `pipeline/` holds the main Prefect flow and preprocessing runner.
- `tests/` contains unit tests for the cleaning, validation, normalization, and preprocessing layers.
- `artifacts/` stores generated outputs such as saved pipelines.

## Requirements

- Python 3.11 or newer
- Poetry
- A PostgreSQL database
- A MongoDB Atlas cluster or another MongoDB-compatible source if your scraper depends on it
- Telegram bot credentials for notifications

## Environment Setup

Create a `.env` file from the example file and fill in your values:

```bash
cp .env.example .env
```

Required environment variables:

- `MONGO_URI`
- `POSTGRES`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

If an environment variable is not set, the project can also read the matching Prefect Secret block.

## Installation

```bash
poetry install
```

If you are using Playwright for the scrapers, install the browser binaries as well:

```bash
poetry run playwright install
```

## Running the Pipeline

Run the full pipeline from the project root:

```bash
poetry run python pipeline/main.py
```

This will:

1. Load the configured scraper profiles from `scrapers/configs/`.
2. Scrape listings from each source.
3. Ingest the raw records into the database.
4. Transform, clean, and preprocess the data.
5. Save train, validation, and test tables to PostgreSQL.
6. Persist the preprocessing pipeline to `artifacts/pipelines/preprocessing_pipeline.joblib`.

## Preprocessing Only

If you already have a cleaned `clean_properties` table and only want to rebuild the feature pipeline and splits, run:

```bash
poetry run python pipeline/run_preprocessing.py
```

## Testing

Run the test suite with:

```bash
poetry run pytest
```

The tests cover the cleaning rules, validation logic, normalization helpers, and preprocessing pipeline behavior.

## Docker

The project includes a container setup for running the pipeline inside Docker.

```bash
docker compose -f Docker-compose.yaml up --build
```

## Outputs

After a successful run, you should expect to see:

- cleaned and modeled tables in PostgreSQL
- saved train, validation, and test splits
- a persisted preprocessing pipeline under `artifacts/pipelines/`
- Telegram status messages for success or failure

## Notes

- The project is structured around real pipeline work, so the safest way to extend it is to add or update one stage at a time.
- If you change the schema or cleaning rules, update the matching tests in `tests/` as well.
