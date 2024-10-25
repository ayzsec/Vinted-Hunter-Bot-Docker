from pymongo import MongoClient
from typing import Dict, Any
from loguru import logger as log

def get_database():
    """Get MongoDB database connection"""
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['vinted_bot']
        return db
    except Exception as e:
        log.error(f"Failed to connect to MongoDB: {e}")
        raise

def init_collections(db):
    """Initialize collections with indexes"""
    try:
        # Create indexes
        db.subscriptions.create_index("id", unique=True)
        db.items.create_index("id", unique=True)
    except Exception as e:
        log.error(f"Failed to initialize collections: {e}")
        raise
