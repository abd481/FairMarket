# In the name of Allah , The most gracious , The most merciful 
import asyncio
import json
import random
import requests
import sys
from pathlib import Path
from prefect import flow, task

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scrapers.engine import scrape
from data.processing.transform import transform
from data.ingestion.ingest import ingest
from data.processing.cleaning import clean
from pipeline.run_preprocessing import run_preprocessing
from utils.secrets import get_secret

def load_config(path):
    """Load scraper configuration from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def send_telegram(message: str):
    token = get_secret('TELEGRAM_BOT_TOKEN','telegram-bot-token')
    chat_id = get_secret('TELEGRAM_CHAT_ID','telegram-chat-id')
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message}
        )
    except Exception as e:
        print(f"⚠️ Telegram alert failed: {e}")


def on_failure(flow, flow_run, state):
    send_telegram(
        f"❌ Pipeline FAILED\n"
        f"Flow: {flow.name}\n"
        f"Run: {flow_run.name}\n"
        f"Error: {state.message}"
    )


def on_success(flow, flow_run, state):
    send_telegram(
        f"✅ Pipeline COMPLETED\n"
        f"Flow: {flow.name}\n"
        f"Run: {flow_run.name}"
    )


@task(name="scrape_listings")
async def run_scrape(config, pages):
    return await scrape(config, max_pages=pages)


@task(name="ingest_listings")
def run_ingest(raw_listings):
    return ingest(raw_listings)


@task(name="transform_listings")
def run_transform():
    transform()


@task(name="clean_listings")
def run_clean():
    clean()


@task(name="preprocess_features")
def run_preprocess():
    run_preprocessing()


@flow(
    name="real_estate_pipeline",
    on_failure=[on_failure],
    on_completion=[on_success]
)
async def main():
    configs = [
        load_config(PROJECT_ROOT / "scrapers" / "configs" / "bayut.json"),
        load_config(PROJECT_ROOT / "scrapers" / "configs" / "olx.json"),
    ]

    all_listings = []

    for config in configs:
        pages = random.randint(5,7)
        print(f"🔄 Scraping {pages} pages...")
        listings = await run_scrape(config, pages)
        if listings:
            all_listings.extend(listings)

    if not all_listings:
        send_telegram("⚠️ Pipeline ran but no new listings were scraped")
        print("❌ No data scraped")
        return

    print(f"\n✅ Scraper collected {len(all_listings)} listings")

    print("\n🔄 Running validation pipeline...")
    results = run_ingest(all_listings)

    run_transform()
    run_clean()
    run_preprocess()

    send_telegram(
        f"📊 Pipeline Summary\n"
        f"Total: {results['total']}\n"
        f"✅ Approved: {results['new']}\n"
        f"❌ Rejected: {results['rejected']}\n"
        f"⏭️ Duplicates: {results['duplicate']}\n"
        f"⚠️ Errors: {results['error']}"
    )

    print("\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)
    print(f"Total processed:  {results['total']}")
    print(f"✅ Approved:      {results['new']}")
    print(f"❌ Rejected:      {results['rejected']}")
    print(f"⏭️  Duplicates:    {results['duplicate']}")
    print(f"⚠️  Errors:       {results['error']}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
