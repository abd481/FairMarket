# In the name of Allah , The most gracious , The most merciful 

import os
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

from data.normalize import normalize_row
from data.checksum import generate_checksum
from data.schema import Property
from data.rules import PropertyRules
from data.property_logger import property_logger, logger
from utils.secrets import get_secret
load_dotenv()


class DataPipeline:
    """
    Safe incremental ingestion pipeline.

    Guarantees:
    - No KeyErrors
    - No missing status crashes
    - Safe deduplication (batch + DB)
    - Stable output schema for UI / main.py
    """

    def __init__(self):
        try:
            mongo_uri = get_secret('MONGO_URI','mongo-uri')
            if not mongo_uri:
                raise ValueError("MONGO_URI missing")

            self.client = MongoClient(mongo_uri)
            self.db = self.client["real_estate_db"]

            self.raw_listings = self.db["raw_listings"]
            self.rejected_listings = self.db["rejected_listings"]
            self.duplicate_listings = self.db["duplicate_listings"]
            self.processing_stats = self.db["processing_stats"]

            self.raw_listings.create_index(
                [("checksum", ASCENDING)],
                unique=True,
                sparse=True
            )

            logger.info("Pipeline initialized")

        except Exception as e:
            logger.error(f"Init failed: {str(e)}")
            raise

    def _log_schema_rejection(self, normalized: dict, error: str) -> None:
        """Log Gate 1 failures directly to MongoDB since we have no prop object."""
        try:
            self.rejected_listings.insert_one({
                "source": normalized.get("source", "unknown"),
                "rejected_at": datetime.now(),
                "gate": "gate_1_schema",
                "failed_rules": [f"Schema validation failed: {error}"],
                "listing_data": normalized
            })
        except Exception as e:
            logger.error(f"Failed to log schema rejection: {str(e)}")

    def process_single_listing(self, raw_row: Dict[str, Any], seen_checksums: set) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            normalized = normalize_row(raw_row)
            checksum = generate_checksum(normalized)
            link = normalized.get("link", "unknown")

            # 1. batch duplicate
            if checksum in seen_checksums:
                return True, "duplicate", {"link": link}

            seen_checksums.add(checksum)

            # 2. DB duplicate
            if self.raw_listings.find_one({"checksum": checksum}):
                self.duplicate_listings.insert_one({
                    "link": link,
                    "checksum": checksum,
                    "seen_at": datetime.now(),
                    "raw_data": raw_row
                })
                return True, "duplicate", {"link": link}

            # 3. Gate 1 — schema validation
            try:
                prop = Property(**normalized)
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"❌ Gate 1 failed | Link: {link} | Error: {error_msg}")
                self._log_schema_rejection(normalized, error_msg)
                return False, "rejected", {"error": error_msg}

            # 4. Gate 2 — business rules
            is_valid, errors = PropertyRules.validate(prop)
            if not is_valid:
                logger.warning(f"❌ Gate 2 failed | Link: {link} | Rules: {errors}")
                property_logger.log_rejection(prop, errors)
                return True, "rejected", {"errors": errors}

            # 5. store approved listing
            property_logger.log_approved(prop, checksum)
            return True, "new", {"link": link}

        except Exception as e:
            logger.error(f"Pipeline crash: {str(e)}", exc_info=True)
            return False, "error", {"error": str(e)}

    def process_batch(self, raw_listings: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = {
            "total": len(raw_listings),
            "new": 0,
            "duplicate": 0,
            "rejected": 0,
            "error": 0,
            "timestamp": datetime.now()
        }

        seen = set()

        for row in raw_listings:
            success, status, _ = self.process_single_listing(row, seen)

            if status in results:
                results[status] += 1
            else:
                results["error"] += 1

        self.processing_stats.insert_one(results)
        return results


pipeline = DataPipeline()


def ingest(raw_listings: List[Dict[str, Any]]) -> Dict[str, Any]:
    return pipeline.process_batch(raw_listings)