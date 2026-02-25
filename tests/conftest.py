"""Pytest configuration and fixtures."""

import httpx
import mongomock_motor
import pytest
from httpx import ASGITransport

from watersvc.app import app
from watersvc.database.connection import get_database


@pytest.fixture
async def mock_db():
    """In-memory MongoDB instance, fresh per test."""
    mongo_client = mongomock_motor.AsyncMongoMockClient()
    return mongo_client["watersvc_test"]


@pytest.fixture
async def client(mock_db):
    """Async test client with mocked database dependency."""

    async def override_get_database():
        return mock_db

    app.dependency_overrides[get_database] = override_get_database

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def integration_client():
    """Async test client using real MongoDB. Auto-skips if unreachable."""
    from motor.motor_asyncio import AsyncIOMotorClient

    from watersvc.config import get_settings
    from watersvc.database.connection import db as motor_db

    try:
        settings = get_settings()
        uri = settings.mongodb_uri
    except Exception:
        pytest.skip("MONGODB_URI not configured")
        return

    # Verify connectivity before starting
    mc = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
    try:
        await mc.admin.command("ping")
    except Exception:
        mc.close()
        pytest.skip("Cannot reach MongoDB")
        return

    # Pre-test cleanup (idempotent — handles leftovers from prior failed runs)
    real_db = mc[settings.mongodb_database]
    await real_db.user_profile.delete_one({"user_id": "default"})
    await real_db.water_intakes.delete_many({"user_id": "default"})
    mc.close()
    motor_db.client = None  # reset singleton so app opens a fresh connection

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    # Post-test cleanup
    mc = AsyncIOMotorClient(uri)
    real_db = mc[settings.mongodb_database]
    await real_db.user_profile.delete_one({"user_id": "default"})
    await real_db.water_intakes.delete_many({"user_id": "default"})
    mc.close()
    motor_db.client = None  # reset for tests that run after
