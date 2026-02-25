"""One-time database setup script to create indexes."""

import asyncio

from watersvc.database.connection import get_database
from watersvc.database.service import WaterIntakeService


async def setup_database():
    """Create indexes for optimal query performance."""
    print("🔧 Setting up MongoDB database...")
    print()

    try:
        # Get database connection
        db = await get_database()
        service = WaterIntakeService(db)

        print("📊 Creating indexes...")
        await service.ensure_indexes()

        print("✅ Indexes created successfully!")
        print()
        print("Database setup complete! Your indexes:")
        print("  • water_intakes: {user_id: 1, local_date: -1, timestamp: -1}")
        print("  • water_intakes: {user_id: 1, timestamp: -1}")
        print("  • user_profile: {user_id: 1} (unique)")
        print()
        print("✨ Your database is ready to use!")

    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        print()
        print("Please check:")
        print("  • MONGODB_URI is set in .env file")
        print("  • MongoDB Atlas cluster is running")
        print("  • Network access is configured correctly")
        raise


if __name__ == "__main__":
    asyncio.run(setup_database())
