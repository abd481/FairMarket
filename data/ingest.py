# In the name of Allah , The most gracious , The most merciful

import os
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

from data.normalize import normalize_row
from data.checksum import generate_checksum, check_and_handle, ListingStatus
from data.schema import Property
from data.rules import PropertyRules
from data.property_logger import property_logger, logger

load_dotenv()


def generate_property_fingerprint(normalized_row: dict) -> str:
    """
    Generate a hash from the PHYSICAL property identity — WITHOUT price.

    Why separate from checksum?
    - checksum  = full content hash (link + price + area) → detects ANY change
    - fingerprint = property identity hash (location + area + beds + baths + type)
                    → detects "same apartment, price changed"

    Example:
        Listing A: Maadi, 120sqm, 3bed, 2bath, apartment, price=2_000_000
        Listing B: Maadi, 120sqm, 3bed, 2bath, apartment, price=1_800_000 (price dropped)

        → Same fingerprint, different checksum → PRICE_UPDATED (not a new listing)
    """
    import hashlib
    stable = {
        "location":      str(normalized_row.get("location", "") or "").strip().lower(),
        "area":          str(normalized_row.get("area", "") or ""),
        "beds":          str(normalized_row.get("beds", "") or ""),
        "baths":         str(normalized_row.get("baths", "") or ""),
        "property_type": str(normalized_row.get("property_type", "") or "").strip().lower(),
    }
    content = "|".join(f"{k}:{v}" for k, v in sorted(stable.items()))
    return hashlib.md5(content.encode()).hexdigest()


class DataPipeline:
    """
    Safe incremental ingestion pipeline.

    Deduplication has THREE layers now:

    Layer 1 — Batch dedup (in-memory set of checksums)
        Catches exact duplicates within the same scrape run
        before touching the DB at all.

    Layer 2 — check_and_handle (DB-level, per link)
        NEW      → never seen this link before
        DUPLICATE → same link, same content (price/area unchanged) → skip
        UPDATED   → same link, content changed → store as new version

    Layer 3 — Property fingerprint (DB-level, per physical property)
        Catches "same apartment listed again with a different link but same specs"
        This is common on Egyptian platforms (seller reposts same unit)
        Result: PRICE_UPDATED → store new version, mark old as superseded
    """

    def __init__(self):
        try:
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                raise ValueError("MONGO_URI missing from .env")

            self.client = MongoClient(mongo_uri)
            self.db = self.client["real_estate_db"]

            self.raw_listings        = self.db["raw_listings"]
            self.rejected_listings   = self.db["rejected_listings"]
            self.duplicate_listings  = self.db["duplicate_listings"]
            self.processing_stats    = self.db["processing_stats"]

            # Unique index on checksum — DB-level guarantee against exact dupes
            self.raw_listings.create_index(
                [("checksum", ASCENDING)],
                unique=True,
                sparse=True
            )

            # Index on fingerprint for fast same-property lookups
            self.raw_listings.create_index(
                [("property_fingerprint", ASCENDING)],
                sparse=True
            )

            # Index on link for check_and_handle lookups
            self.raw_listings.create_index(
                [("link", ASCENDING)],
                sparse=True
            )

            logger.info("Pipeline initialized successfully")

        except Exception as e:
            logger.error(f"Pipeline init failed: {str(e)}")
            raise

    def _log_schema_rejection(self, normalized: dict, error: str) -> None:
        """Log Gate 1 schema failures — no Property object exists yet so we log raw."""
        try:
            self.rejected_listings.insert_one({
                "source":       normalized.get("source", "unknown"),
                "rejected_at":  datetime.now(),
                "gate":         "gate_1_schema",
                "failed_rules": [f"Schema validation failed: {error}"],
                "listing_data": normalized
            })
        except Exception as e:
            logger.error(f"Failed to log schema rejection: {str(e)}")

    def _store_listing(self, prop: Property, checksum: str, fingerprint: str) -> None:
        """Insert approved listing into raw_listings."""
        property_logger.log_approved(prop, checksum)
        # log_approved handles the insert — we just also save the fingerprint
        self.raw_listings.update_one(
            {"checksum": checksum},
            {"$set": {"property_fingerprint": fingerprint}},
        )

    def _mark_superseded(self, old_fingerprint: str) -> None:
        """
        Mark old versions of the same physical property as superseded.
        We keep them (immutability) but flag them so the clean layer
        knows to only use the latest version.
        """
        self.raw_listings.update_many(
            {"property_fingerprint": old_fingerprint},
            {"$set": {"status": "superseded", "superseded_at": datetime.now()}}
        )

    def process_single_listing(
        self,
        raw_row: Dict[str, Any],
        seen_checksums: set,
        seen_fingerprints: set
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process one listing through all deduplication + validation layers.

        Returns:
            (success: bool, status: str, detail: dict)

        Status values: "new" | "duplicate" | "price_updated" | "rejected" | "error"
        """
        try:
            normalized   = normalize_row(raw_row)
            checksum     = generate_checksum(normalized)
            fingerprint  = generate_property_fingerprint(normalized)
            link         = normalized.get("link", "unknown")

            # ── Layer 1: Batch-level exact duplicate ──────────────────────────
            if checksum in seen_checksums:
                logger.debug(f"Batch dupe skipped | link: {link}")
                return True, "duplicate", {"link": link}

            seen_checksums.add(checksum)

            # ── Layer 2: DB-level check via check_and_handle ──────────────────
            status = check_and_handle(normalized, checksum)

            if status == ListingStatus.DUPLICATE:
                self.duplicate_listings.insert_one({
                    "link":       link,
                    "checksum":   checksum,
                    "seen_at":    datetime.now(),
                    "raw_data":   raw_row
                })
                logger.debug(f"DB dupe skipped | link: {link}")
                return True, "duplicate", {"link": link}

            # UPDATED = same link, price/area changed → fall through to store
            # NEW     = brand new link → fall through to store
            # Both cases proceed to validation gates below.

            # ── Layer 3: Same physical property, different link / price ────────
            # (e.g. seller deleted and reposted at a new price with a new URL)
            price_updated = False

            if fingerprint not in seen_fingerprints:
                existing_by_fingerprint = self.raw_listings.find_one(
                    {
                        "property_fingerprint": fingerprint,
                        "status":               {"$ne": "superseded"}
                    }
                )
                if existing_by_fingerprint:
                    existing_price = (
                        existing_by_fingerprint
                        .get("listing_data", {})
                        .get("price")
                    )
                    incoming_price = normalized.get("price")
                    if existing_price != incoming_price:
                        # Same apartment, price changed — store new version
                        logger.info(
                            f"Price update detected | link: {link} | "
                            f"{existing_price} → {incoming_price}"
                        )
                        self._mark_superseded(fingerprint)
                        price_updated = True
                    else:
                        # Same apartment, same price, different link → duplicate
                        logger.debug(f"Same-property dupe skipped | link: {link}")
                        self.duplicate_listings.insert_one({
                            "link":                 link,
                            "checksum":             checksum,
                            "property_fingerprint": fingerprint,
                            "reason":               "same_property_same_price",
                            "seen_at":              datetime.now(),
                            "raw_data":             raw_row
                        })
                        return True, "duplicate", {"link": link}

            seen_fingerprints.add(fingerprint)

            # ── Gate 1: Schema validation ──────────────────────────────────────
            try:
                prop = Property(**normalized)
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Gate 1 failed | link: {link} | {error_msg}")
                self._log_schema_rejection(normalized, error_msg)
                return False, "rejected", {"error": error_msg}

            # ── Gate 2: Business rules validation ─────────────────────────────
            is_valid, errors = PropertyRules.validate(prop)
            if not is_valid:
                logger.warning(f"Gate 2 failed | link: {link} | rules: {errors}")
                property_logger.log_rejection(prop, errors)
                return True, "rejected", {"errors": errors}

            # ── Store approved listing ─────────────────────────────────────────
            self._store_listing(prop, checksum, fingerprint)

            final_status = "price_updated" if price_updated else "new"
            logger.info(f"Stored listing | status: {final_status} | link: {link}")
            return True, final_status, {"link": link}

        except Exception as e:
            logger.error(f"Pipeline crash on row: {str(e)}", exc_info=True)
            return False, "error", {"error": str(e)}

    def process_batch(self, raw_listings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a full scrape batch.

        Returns a stats dict logged to processing_stats collection.
        """
        results = {
            "total":         len(raw_listings),
            "new":           0,
            "duplicate":     0,
            "price_updated": 0,   # same property, price changed
            "rejected":      0,
            "error":         0,
            "timestamp":     datetime.now()
        }

        seen_checksums   = set()
        seen_fingerprints = set()

        for row in raw_listings:
            _, status, _ = self.process_single_listing(row, seen_checksums, seen_fingerprints)

            if status in results:
                results[status] += 1
            else:
                results["error"] += 1

        self.processing_stats.insert_one(results)

        logger.info(
            f"Batch done | new={results['new']} | "
            f"price_updated={results['price_updated']} | "
            f"dupes={results['duplicate']} | "
            f"rejected={results['rejected']} | "
            f"errors={results['error']}"
        )
        return results


pipeline = DataPipeline()


def ingest(raw_listings: List[Dict[str, Any]]) -> Dict[str, Any]:
    return pipeline.process_batch(raw_listings)