# In the name of Allah , The most gracious , The most merciful 
import hashlib
import os
from datetime import datetime
from pymongo import MongoClient
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["real_estate_db"]
raw_collection = db["raw_listings"]



class ListingStatus(Enum):
    NEW = "new"
    DUPLICATE = "duplicate"
    UPDATED = "updated"

def generate_checksum(normalized_row: dict) -> str:
    """
    Generate a hash from stable listing content.
    We use price + area + link because:
    - link identifies the listing
    - price + area detect if content changed (versioning)
    """
    stable = {
        "link": normalized_row.get("link", ""),
        "price": str(normalized_row.get("price", "")),
        "area": str(normalized_row.get("area", "")),
    }
    content = "|".join(f"{k}:{v}" for k, v in sorted(stable.items()))
    return hashlib.md5(content.encode()).hexdigest()


def check_and_handle(normalized_row: dict, checksum: str) -> str:
    """
    Compare incoming listing against MongoDB raw layer.

    Returns:
        "new"       → never seen before, store it
        "duplicate" → exact same content, skip it
        "updated"   → same link but content changed, store as new version
    """
    link = normalized_row.get("link", "")

    # look for any existing listing with same link
    existing = raw_collection.find_one({"link": link})

    if not existing:
        return ListingStatus.NEW

    # Use .get() to handle old documents that don't have checksum field
    existing_checksum = existing.get("checksum")
    if existing_checksum == checksum:
        return ListingStatus.DUPLICATE

    return ListingStatus.UPDATED

