from sqlalchemy import create_engine
from pymongo import MongoClient
from utils.secrets import get_secret

_client = None
_pg_engine = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        mongo_uri = get_secret("MONGO_URI", "mongo-uri")
        _client = MongoClient(mongo_uri)
    return _client


def get_database(db_name: str = "real_estate_db"):
    return get_mongo_client()[db_name]


def get_collection(collection_name: str, db_name: str = "real_estate_db"):
    return get_database(db_name)[collection_name]


def get_pg_engine():
    """Lazily create (and cache) the PostgreSQL SQLAlchemy engine."""
    global _pg_engine
    if _pg_engine is None:
        _pg_engine = create_engine(get_secret("POSTGRES", "postgres"))
    return _pg_engine
