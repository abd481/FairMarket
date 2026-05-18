# In the name of Allah , The most gracious , The most merciful 
import logging
import os
from datetime import datetime
from pymongo import MongoClient
from typing import List, Optional
from dotenv import load_dotenv
from utils.secrets import get_secret
# Load environment variables
load_dotenv()

# Configure logging
LOG_FILE = "logs/property_processing.log"
os.makedirs("logs", exist_ok=True)

# Create logger
logger = logging.getLogger("PropertyLogger")
logger.setLevel(logging.DEBUG)

# Console handler (for real-time output)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(console_formatter)

# File handler (for historical records)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - [%(name)s] - %(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


class PropertyLogger:
    """
    Centralized logging system for property processing operations.
    
    Collections structure:
    - rejected_listings: Properties that failed validation (with metadata fields: link, source, scraped_at)
    - raw_listings: Properties that passed validation (with metadata fields: link, source, scraped_at)
    - property_stats: Aggregated statistics per source
    
    Handles logging to console, file, and MongoDB.
    """
    
    def __init__(self):
        """Initialize MongoDB connection and collections."""
        try:
            mongo_uri = get_secret('MONGO_URI','mongo-uri')
            

            if not mongo_uri:
                logger.warning("MONGO_URI not found in .env file")
                self.client = None
                self.db = None
                self.rejected_collection = None
                self.raw_collection = None
                self.stats_collection = None
            else:
                self.client = MongoClient(mongo_uri)
                self.db = self.client["real_estate_db"]
                self.rejected_collection = self.db["rejected_listings"]
                self.raw_collection = self.db["raw_listings"]
                self.stats_collection = self.db["property_stats"]
                logger.info("✅ Connected to MongoDB successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
            self.rejected_collection = None
            self.raw_collection = None
            self.stats_collection = None
    
    def log_rejection(self, prop, failed_rules: List[str]) -> Optional[str]:
        """
        Log a rejected property to console, file, and MongoDB.
        
        Args:
            prop: Property object that failed validation
            failed_rules: List of validation rules that failed
            
        Returns:
            MongoDB document ID if successful, None otherwise
        """
        try:
            # Prepare document with metadata as searchable fields
            document = {
                "link": prop.link,
                "source": prop.source,
                "scraped_at": prop.scraped_at,
                "rejected_at": datetime.now(),
                "failed_rules": failed_rules,
                "listing_data": prop.model_dump()
            }
            
            # Log to console and file
            logger.warning(
                f"Property REJECTED | Source: {prop.source} | Price: {prop.price} | "
                f"Failed Rules: {', '.join(failed_rules[:2])}{'...' if len(failed_rules) > 2 else ''}"
            )
            
            # Save to MongoDB
            if self.rejected_collection is not None:
                result = self.rejected_collection.insert_one(document)
                logger.debug(f"Saved rejection to MongoDB: {result.inserted_id}")
                
                # Update rejection statistics
                self._update_rejection_stats(prop.source)
                
                return str(result.inserted_id)
            else:
                logger.warning("MongoDB connection unavailable - rejection not saved to database")
                return None
                
        except Exception as e:
            logger.error(f"Failed to log rejection: {str(e)}", exc_info=True)
            return None
    
    def log_approved(self, prop,checksum:str) -> Optional[str]:
        """
        Log an approved property to MongoDB raw_listings collection.
        
        Args:
            prop: Property object that passed validation
            
        Returns:
            MongoDB document ID if successful, None otherwise
        """
        try:
            # Prepare document with metadata as searchable fields
            document = {
                "checksum" : checksum , 
                "link": prop.link,
                "source": prop.source,
                "scraped_at": prop.scraped_at,
                "listing_data": prop.model_dump()
            }
            
            # Log to console and file
            logger.info(
                f"Property APPROVED ✅ | Source: {prop.source} | Price: {prop.price} | "
                f"Location: {prop.location} | Link: {prop.link}"
            )
            
            # Save to raw_listings collection
            if self.raw_collection is not None:
                result = self.raw_collection.insert_one(document)
                logger.debug(f"Saved approved property to raw_listings: {result.inserted_id}")
                
                # Update approval statistics
                self._update_approval_stats(prop.source)
                
                return str(result.inserted_id)
            else:
                logger.warning("MongoDB connection unavailable - approved property not saved to database")
                return None
                
        except Exception as e:
            logger.error(f"Failed to log approved property: {str(e)}", exc_info=True)
            return None
    
    def _update_rejection_stats(self, source: str) -> None:
        """Update rejection count statistics per source."""
        try:
            if self.stats_collection is None:
                return
                
            self.stats_collection.update_one(
                {"source": source, "type": "rejection"},
                {
                    "$inc": {"count": 1},
                    "$set": {"last_updated": datetime.now()}
                },
                upsert=True
            )
            logger.debug(f"Updated rejection stats for source: {source}")
        except Exception as e:
            logger.error(f"Failed to update rejection stats: {str(e)}")
    
    def _update_approval_stats(self, source: str) -> None:
        """Update approval count statistics per source."""
        try:
            if self.stats_collection is None:
                return
                
            self.stats_collection.update_one(
                {"source": source, "type": "approval"},
                {
                    "$inc": {"count": 1},
                    "$set": {"last_updated": datetime.now()}
                },
                upsert=True
            )
            logger.debug(f"Updated approval stats for source: {source}")
        except Exception as e:
            logger.error(f"Failed to update approval stats: {str(e)}")
    
    def log_scraping_start(self, source: str, max_pages: int) -> None:
        """Log the start of a scraping operation."""
        logger.info(f"🔄 Starting scrape | Source: {source} | Max Pages: {max_pages}")
    
    def log_scraping_end(self, source: str, total_scraped: int) -> None:
        """Log the completion of a scraping operation."""
        logger.info(f"✅ Scraping completed | Source: {source} | Total Properties: {total_scraped}")
    
    def log_scraping_error(self, source: str, link: str, error: str) -> None:
        """Log errors during scraping."""
        logger.error(f"❌ Scraping error | Source: {source} | Link: {link} | Error: {error}")
    
    def get_stats(self, source: Optional[str] = None) -> dict:
        """
        Get statistics from MongoDB.
        
        Args:
            source: Specific source to get stats for (optional)
            
        Returns:
            Dictionary with approval/rejection stats
        """
        try:
            if not self.stats_collection:
                logger.warning("Cannot retrieve stats - MongoDB unavailable")
                return {}
            
            query = {"source": source} if source else {}
            stats = list(self.stats_collection.find(query))
            logger.info(f"Retrieved stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Failed to retrieve stats: {str(e)}")
            return {}

