# In the name of Allah , The most gracious , The most merciful 
import asyncio
import json
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import from data folder
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import scrape
from data.transform import transform
from data.ingest import ingest




def load_config(path):
    """Load scraper configuration from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def main():
    """
    Main scraping and pipeline execution.
    
    Flow:
    1. Load configuration
    2. Run scraper to collect raw data
    3. Pass data to validation pipeline
    4. Pipeline handles: normalize → dedupe → validate → store
    """
    config = load_config(Path(__file__).parent / "configs" / "olx.json")
    
    print("🔄 Starting scraper...")
    # Step 1: Scrape raw data
    raw_listings = await scrape(config, max_pages=2)
    
    if not raw_listings:
        print("❌ No data scraped")
        return
    
    print(f"\n✅ Scraper collected {len(raw_listings)} listings")
    
    # Step 2: Pass to validation pipeline
    print("\n🔄 Running validation pipeline...")
    results = ingest(raw_listings)
    # Transform properties before move to PostgreSQL
    transform()
    
    # Step 3: Display summary
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

