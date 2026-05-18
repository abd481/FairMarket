# In the name of Allah, The Most Gracious, The Most Merciful

import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from sqlalchemy import create_engine, text
from utils.secrets import get_secret
load_dotenv()

mongo_client = MongoClient(get_secret('MONGO_URI','mongo-uri'))
raw_collection = mongo_client["real_estate_db"]["raw_listings"]

engine = create_engine(get_secret('POSTGRES','postgres'))

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS properties (
    id                SERIAL PRIMARY KEY,
    checksum          TEXT UNIQUE NOT NULL,
    price             INTEGER,
    location          TEXT,
    title             TEXT,
    beds              TEXT,
    baths             INTEGER,
    area              FLOAT,
    property_type     TEXT,
    furnishing        TEXT,
    amenities         TEXT,
    link              TEXT,
    reactivated_date  TIMESTAMP,
    source            TEXT,
    scraped_at        TIMESTAMP,
    transformed_at    TIMESTAMP
);
"""


def safe_int(value):
    """For price, baths — returns None if not a valid number."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_beds(value):
    """For beds — keeps 'Studio' as text, converts numbers, rejects garbage."""
    if value is None:
        return None
    try:
        return str(int(value))  # 3 → "3"
    except (ValueError, TypeError):
        if isinstance(value, str) and value.strip().lower() == "studio":
            return "Studio"
        return None


def transform():

    with engine.connect() as conn:

        conn.execute(text(CREATE_TABLE))
        conn.commit()

        print("✅ Table ready")

        docs = list(
            raw_collection.find(
                {"transformed": {"$ne": True}}
            )
        )

        print(f"📦 Found {len(docs)} untransformed documents")

        if not docs:
            print("⚠️ Nothing to transform")
            return

        inserted = 0
        skipped = 0
        errors = 0

        for doc in docs:

            try:

                data = doc.get("listing_data", {})

                amenities = data.get("amenities")

                if isinstance(amenities, list):
                    amenities = ", ".join(amenities)

                flat = {
                    "checksum":         doc.get("checksum"),
                    "price":            safe_int(data.get("price")),
                    "location":         data.get("location"),
                    "title":            data.get("title"),
                    "beds":             safe_beds(data.get("beds")),
                    "baths":            safe_int(data.get("baths")),
                    "area":             data.get("area"),
                    "property_type":    data.get("property_type"),
                    "furnishing":       data.get("furnishing"),
                    "amenities":        amenities,
                    "link":             data.get("link"),
                    "reactivated_date": data.get("reactivated_date"),
                    "source":           doc.get("source"),
                    "scraped_at":       doc.get("scraped_at"),
                    "transformed_at":   datetime.now(),
                }

                if not flat["checksum"]:
                    print("⚠️ Skipping document with no checksum")
                    skipped += 1
                    continue

                conn.execute(text("""
                    INSERT INTO properties (
                        checksum, price, location, title,
                        beds, baths, area, property_type,
                        furnishing, amenities, link,
                        reactivated_date, source, scraped_at, transformed_at
                    )
                    VALUES (
                        :checksum, :price, :location, :title,
                        :beds, :baths, :area, :property_type,
                        :furnishing, :amenities, :link,
                        :reactivated_date, :source, :scraped_at, :transformed_at
                    )
                    ON CONFLICT (checksum) DO NOTHING
                """), flat)

                conn.commit()

                raw_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"transformed": True}}
                )

                inserted += 1

            except Exception as e:

                conn.rollback()

                print(f"❌ Error | link: {doc.get('listing_data', {}).get('link')} | {e}")

                errors += 1

        print("\n✅ Transform done!")
        print(f"   Inserted:  {inserted}")
        print(f"   Skipped:   {skipped}")
        print(f"   Errors:    {errors}")


if __name__ == "__main__":
    transform()