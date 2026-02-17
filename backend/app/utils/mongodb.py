"""
MongoDB utility for connection management.
Used for storing video metadata, processing logs, and non-relational data.
"""
from pymongo import MongoClient
from app.config import Config

class MongoDB:
    """MongoDB connection manager."""
    
    _client = None
    _db = None
    
    @classmethod
    def get_client(cls):
        """Get MongoDB client instance."""
        if cls._client is None:
            cls._client = MongoClient(
                host=Config.MONGODB_HOST,
                port=Config.MONGODB_PORT
            )
        return cls._client
    
    @classmethod
    def get_database(cls):
        """Get MongoDB database instance."""
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[Config.MONGODB_DB]
        return cls._db
    
    @classmethod
    def close_connection(cls):
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

# Initialize MongoDB connection
mongodb = MongoDB()

