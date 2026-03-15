"""One-time database setup script to create indexes."""

import asyncio
import logging

from watersvc.database.connection import get_database
from watersvc.database.service import WaterIntakeService

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def setup_database():
    """Create indexes for optimal query performance."""
    logger.info("Setting up MongoDB database...")

    try:
        db = await get_database()
        service = WaterIntakeService(db)

        logger.info("Creating indexes...")
        await service.ensure_indexes()

        logger.info("Indexes created successfully")
        logger.info("Indexes: water_intakes(user_id, local_date, timestamp), user_profile(user_id unique)")

    except Exception as e:
        logger.error("Error setting up database: %s", e)
        logger.error("Check: MONGODB_URI in .env, Atlas cluster status, and network access")
        raise


if __name__ == "__main__":
    asyncio.run(setup_database())
