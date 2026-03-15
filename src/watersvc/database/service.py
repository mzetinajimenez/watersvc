"""Database service layer for water intake tracking operations."""

from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class WaterIntakeService:
    """Service class for water intake database operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize service with database instance."""
        self.db = db
        self.intakes = db.water_intakes
        self.profiles = db.user_profile

    # Profile operations
    async def get_profile(self, user_id: str) -> dict | None:
        """Get user profile by user_id."""
        return await self.profiles.find_one({"user_id": user_id})

    async def create_profile(self, profile_data: dict) -> dict:
        """Create new user profile."""
        result = await self.profiles.insert_one(profile_data)
        profile_data["_id"] = result.inserted_id
        return profile_data

    async def update_profile(self, user_id: str, update_data: dict) -> dict | None:
        """Update user profile with new data."""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.profiles.find_one_and_update(
            {"user_id": user_id},
            {"$set": update_data},
            return_document=True,
        )
        return result

    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile. Returns True if deleted, False if not found."""
        result = await self.profiles.delete_one({"user_id": user_id})
        return result.deleted_count == 1

    # Intake CRUD operations
    async def create_intake(self, intake_data: dict) -> dict:
        """Insert new water intake entry."""
        result = await self.intakes.insert_one(intake_data)
        intake_data["_id"] = result.inserted_id
        return intake_data

    async def get_intake(self, intake_id: str, user_id: str) -> dict | None:
        """Get single intake entry by ID."""
        return await self.intakes.find_one({"_id": ObjectId(intake_id), "user_id": user_id})

    async def update_intake(self, intake_id: str, update_data: dict, user_id: str) -> dict | None:
        """Update water intake entry."""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.intakes.find_one_and_update(
            {"_id": ObjectId(intake_id), "user_id": user_id},
            {"$set": update_data},
            return_document=True,
        )
        return result

    async def delete_intake(self, intake_id: str, user_id: str) -> bool:
        """Delete water intake entry."""
        result = await self.intakes.delete_one({"_id": ObjectId(intake_id), "user_id": user_id})
        return result.deleted_count > 0

    async def list_intakes(
        self,
        user_id: str,
        local_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        List water intake entries with optional filtering.

        Args:
            user_id: User identifier
            local_date: Filter by specific local date (YYYY-MM-DD)
            start_date: Filter by date range start
            end_date: Filter by date range end
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of intake dictionaries
        """
        query = {"user_id": user_id}

        if local_date:
            query["local_date"] = local_date
        elif start_date and end_date:
            query["local_date"] = {"$gte": start_date, "$lte": end_date}  # type: ignore[assignment]
        elif start_date:
            query["local_date"] = {"$gte": start_date}  # type: ignore[assignment]
        elif end_date:
            query["local_date"] = {"$lte": end_date}  # type: ignore[assignment]

        cursor = self.intakes.find(query).sort("timestamp", -1).skip(offset).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_intakes(
        self,
        user_id: str,
        local_date: str | None = None,
    ) -> int:
        """Count total intake entries for a user or specific date."""
        query = {"user_id": user_id}
        if local_date:
            query["local_date"] = local_date
        return await self.intakes.count_documents(query)

    # Aggregation operations
    async def aggregate_daily_total(self, user_id: str, local_date: str) -> tuple[float, int]:
        """
        Aggregate total oz and entry count for a specific local date.

        Returns:
            Tuple of (total_oz, entry_count)
        """
        pipeline = [
            {"$match": {"user_id": user_id, "local_date": local_date}},
            {
                "$group": {
                    "_id": None,
                    "total_oz": {"$sum": "$amount_oz"},
                    "count": {"$sum": 1},
                }
            },
        ]
        result = await self.intakes.aggregate(pipeline).to_list(length=1)  # type: ignore[arg-type]
        if result:
            return result[0]["total_oz"], result[0]["count"]
        return 0.0, 0

    async def aggregate_period_stats(
        self, user_id: str, start_date: str, end_date: str
    ) -> list[dict]:
        """
        Aggregate daily breakdown for a date range.

        Args:
            user_id: User identifier
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of daily aggregations with date, total_oz, and count
        """
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "local_date": {"$gte": start_date, "$lte": end_date},
                }
            },
            {
                "$group": {
                    "_id": "$local_date",
                    "total_oz": {"$sum": "$amount_oz"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        results = await self.intakes.aggregate(pipeline).to_list(length=None)  # type: ignore[arg-type]
        return [{"date": r["_id"], "total_oz": r["total_oz"], "count": r["count"]} for r in results]

    # Index creation (call during initialization or migration)
    async def ensure_indexes(self) -> None:
        """Create necessary indexes for optimal query performance."""
        # Compound index for user + date queries
        await self.intakes.create_index([("user_id", 1), ("local_date", -1), ("timestamp", -1)])
        # Index for time-based queries
        await self.intakes.create_index([("user_id", 1), ("timestamp", -1)])
        # Index for user_profile
        await self.profiles.create_index([("user_id", 1)], unique=True)
