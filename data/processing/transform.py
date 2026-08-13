# In the name of Allah, The Most Gracious, The Most Merciful

from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import text
from utils.db import get_collection, get_pg_engine

load_dotenv()


def get_raw_collection():
    return get_collection("raw_listings")


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

INSERT_ROW = text("""
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
""")


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

    raw_collection = get_raw_collection()

    with get_pg_engine().connect() as conn:

        conn.execute(text(CREATE_TABLE))
        conn.commit()

        print("✅ Table ready")

        docs = list(raw_collection.find({"transformed": {"$ne": True}}))

        print(f"📦 Found {len(docs)} untransformed documents")

        if not docs:
            print("⚠️ Nothing to transform")
            return

        # 1. Build every row up-front (one round-trip for the whole batch).
        rows = []
        skipped = 0

        for doc in docs:
            try:
                data = doc.get("listing_data", {})

                amenities = data.get("amenities")
                if isinstance(amenities, list):
                    amenities = ", ".join(amenities)

                flat = {
                    "checksum": doc.get("checksum"),
                    "price": safe_int(data.get("price")),
                    "location": data.get("location"),
                    "title": data.get("title"),
                    "beds": safe_beds(data.get("beds")),
                    "baths": safe_int(data.get("baths")),
                    "area": data.get("area"),
                    "property_type": data.get("property_type"),
                    "furnishing": data.get("furnishing"),
                    "amenities": amenities,
                    "link": data.get("link"),
                    "reactivated_date": data.get("reactivated_date"),
                    "source": doc.get("source"),
                    "scraped_at": doc.get("scraped_at"),
                    "transformed_at": datetime.now(),
                }
            except Exception as e:
                print(f"❌ Build error | doc: {doc.get('_id')} | {e}")
                raw_collection.update_one(
                    {"_id": doc["_id"]}, {"$set": {"transformed": False}}
                )
                continue

            if not flat["checksum"]:
                print("⚠️ Skipping document with no checksum")
                skipped += 1
                continue

            rows.append((flat, doc["_id"]))

        if not rows:
            print("\n✅ Transform done!")
            print(f"   Inserted:  0")
            print(f"   Skipped:   {skipped}")
            return

        # 2. Insert everything in a single transaction.
        try:
            conn.execute(INSERT_ROW, [flat for flat, _ in rows])
            conn.commit()
        except Exception:
            # 3. Bulk insert aborted the transaction — isolate bad rows.
            conn.rollback()
            print("⚠️ Bulk insert failed — falling back to row-by-row")
            good_rows = []
            for flat, doc_id in rows:
                try:
                    conn.execute(INSERT_ROW, flat)
                    good_rows.append((flat, doc_id))
                except Exception as e:
                    conn.rollback()
                    raw_collection.update_one(
                        {"_id": doc_id}, {"$set": {"transformed": False}}
                    )
                    print(f"❌ Error | link: {flat.get('link')} | {e}")
            conn.commit()
            rows = good_rows

        # 4. Mark Mongo as transformed only after Postgres committed.
        inserted = 0
        for _, doc_id in rows:
            try:
                raw_collection.update_one(
                    {"_id": doc_id}, {"$set": {"transformed": True}}
                )
            except Exception as e:
                print(f"⚠️ Could not mark {doc_id} as transformed: {e}")
            inserted += 1

        print("\n✅ Transform done!")
        print(f"   Inserted:  {inserted}")
        print(f"   Skipped:   {skipped}")
        print(f"   Errors:    {len(docs) - inserted - skipped}")


if __name__ == "__main__":
    transform()
