"""MongoDB connection management for Vercel serverless deployment."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.server_api import ServerApi

from watersvc.config import get_settings


class Database:
    """Singleton database connection manager."""

    client: AsyncIOMotorClient | None = None


db = Database()


async def get_database() -> AsyncIOMotorDatabase:
    """
    Get database instance with lazy initialization.

    This function implements lazy connection for Vercel serverless,
    connecting on first request rather than at import time.

    Returns:
        AsyncIOMotorDatabase instance

    Raises:
        ValueError: If MONGODB_URI environment variable is not set
    """
    if db.client is None:
        settings = get_settings()

        if not settings.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable not set")

        # Optimized connection pool for Vercel serverless
        db.client = AsyncIOMotorClient(
            settings.mongodb_uri,
            server_api=ServerApi("1"),
            maxPoolSize=10,  # Reduced for serverless
            minPoolSize=1,
            maxIdleTimeMS=30000,  # 30s idle timeout
            serverSelectionTimeoutMS=5000,  # 5s timeout
            connectTimeoutMS=10000,  # 10s connection timeout
        )

    return db.client[get_settings().mongodb_database]


async def close_database() -> None:
    """Close database connection."""
    if db.client is not None:
        db.client.close()
        db.client = None
