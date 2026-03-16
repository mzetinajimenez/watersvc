"""Tests for authentication endpoints and JWT handling."""

from unittest.mock import AsyncMock, patch  # noqa: I001

import httpx
import jwt as pyjwt
import mongomock_motor
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from httpx import ASGITransport

from watersvc.app import app
from watersvc.auth.dependencies import get_current_user
from watersvc.auth.jwt import create_access_token, decode_access_token
from watersvc.config import Settings, get_settings
from watersvc.database.connection import get_database


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_JWT_SECRET = "test-secret-key-for-unit-tests-only"


def _test_settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        mongodb_uri="mongodb://localhost:27017",
        jwt_secret=TEST_JWT_SECRET,
        jwt_expiry_hours=1,
        apple_bundle_id="com.mzj.toma-aguita",
        google_client_id="test-google-client-id",
    )


@pytest.fixture
def settings():
    return _test_settings()


@pytest.fixture
async def mock_db():
    mongo_client = mongomock_motor.AsyncMongoMockClient()
    return mongo_client["watersvc_test"]


@pytest.fixture
async def client(mock_db):
    """Async test client with mocked database and settings."""

    async def override_get_database():
        return mock_db

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_settings] = _test_settings

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# JWT unit tests
# ---------------------------------------------------------------------------


class TestJWT:
    def test_create_and_decode(self, settings):
        token = create_access_token("user123", "a@b.com", "anonymous", settings)
        payload = decode_access_token(token, settings)

        assert payload["sub"] == "user123"
        assert payload["email"] == "a@b.com"
        assert payload["provider"] == "anonymous"
        assert "iat" in payload
        assert "exp" in payload

    def test_decode_invalid_token(self, settings):
        with pytest.raises(pyjwt.InvalidTokenError):
            decode_access_token("not.a.valid.token", settings)

    def test_decode_expired_token(self, settings):
        expired_settings = Settings(  # type: ignore[call-arg]
            mongodb_uri="mongodb://localhost:27017",
            jwt_secret=TEST_JWT_SECRET,
            jwt_expiry_hours=0,  # immediate expiry
        )
        token = create_access_token("user123", None, "anonymous", expired_settings)
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_access_token(token, expired_settings)

    def test_decode_wrong_secret(self, settings):
        token = create_access_token("user123", None, "anonymous", settings)
        wrong_settings = Settings(  # type: ignore[call-arg]
            mongodb_uri="mongodb://localhost:27017",
            jwt_secret="wrong-secret-that-is-at-least-32-chars",
        )
        with pytest.raises(pyjwt.InvalidSignatureError):
            decode_access_token(token, wrong_settings)


# ---------------------------------------------------------------------------
# POST /api/auth/anonymous
# ---------------------------------------------------------------------------


class TestAnonymousAuth:
    async def test_new_device(self, client):
        resp = await client.post("/api/auth/anonymous", json={"device_id": "device-aaa"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert data["is_new_user"] is True
        assert data["user_id"]
        assert data["access_token"]

    async def test_returning_device(self, client):
        # First call — create
        resp1 = await client.post("/api/auth/anonymous", json={"device_id": "device-bbb"})
        data1 = resp1.json()
        assert data1["is_new_user"] is True

        # Second call — returning
        resp2 = await client.post("/api/auth/anonymous", json={"device_id": "device-bbb"})
        data2 = resp2.json()
        assert data2["is_new_user"] is False
        assert data2["user_id"] == data1["user_id"]

    async def test_different_devices_different_users(self, client):
        resp1 = await client.post("/api/auth/anonymous", json={"device_id": "dev-1"})
        resp2 = await client.post("/api/auth/anonymous", json={"device_id": "dev-2"})
        assert resp1.json()["user_id"] != resp2.json()["user_id"]

    async def test_empty_device_id_rejected(self, client):
        resp = await client.post("/api/auth/anonymous", json={"device_id": ""})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/auth/apple
# ---------------------------------------------------------------------------

FAKE_APPLE_CLAIMS = {"sub": "apple-sub-001", "email": "user@icloud.com", "email_verified": True}


class TestAppleAuth:
    @patch(
        "watersvc.routers.auth.verify_apple_token",
        new_callable=AsyncMock,
        return_value=FAKE_APPLE_CLAIMS,
    )
    async def test_new_user(self, mock_verify, client):
        resp = await client.post(
            "/api/auth/apple",
            json={"identity_token": "fake-apple-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_new_user"] is True
        assert data["email"] == "user@icloud.com"
        mock_verify.assert_awaited_once()

    @patch(
        "watersvc.routers.auth.verify_apple_token",
        new_callable=AsyncMock,
        return_value=FAKE_APPLE_CLAIMS,
    )
    async def test_returning_user(self, mock_verify, client):
        # First call — new
        resp1 = await client.post("/api/auth/apple", json={"identity_token": "fake-apple-token"})
        uid = resp1.json()["user_id"]

        # Second call — returning
        resp2 = await client.post("/api/auth/apple", json={"identity_token": "fake-apple-token"})
        assert resp2.json()["is_new_user"] is False
        assert resp2.json()["user_id"] == uid

    @patch(
        "watersvc.routers.auth.verify_apple_token",
        new_callable=AsyncMock,
        return_value=FAKE_APPLE_CLAIMS,
    )
    async def test_account_linking(self, mock_verify, client, settings):
        # Step 1: create anonymous user
        anon_resp = await client.post("/api/auth/anonymous", json={"device_id": "link-device"})
        anon_data = anon_resp.json()
        assert anon_data["is_new_user"] is True
        anon_token = anon_data["access_token"]
        anon_uid = anon_data["user_id"]

        # Step 2: link Apple with Bearer token
        resp = await client.post(
            "/api/auth/apple",
            json={"identity_token": "fake-apple-token"},
            headers={"Authorization": f"Bearer {anon_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_new_user"] is False
        assert data["user_id"] == anon_uid  # same user
        assert data["email"] == "user@icloud.com"

    @patch(
        "watersvc.routers.auth.verify_apple_token",
        new_callable=AsyncMock,
        return_value=FAKE_APPLE_CLAIMS,
    )
    async def test_linking_conflict(self, mock_verify, client):
        # User A links Apple
        resp1 = await client.post("/api/auth/apple", json={"identity_token": "fake-apple-token"})
        assert resp1.json()["is_new_user"] is True

        # User B (anonymous) tries to link the same Apple sub
        anon_resp = await client.post("/api/auth/anonymous", json={"device_id": "conflict-device"})
        anon_token = anon_resp.json()["access_token"]

        resp2 = await client.post(
            "/api/auth/apple",
            json={"identity_token": "fake-apple-token"},
            headers={"Authorization": f"Bearer {anon_token}"},
        )
        # Provider already linked to User A → returns existing user A (found by provider lookup)
        assert resp2.status_code == 200
        assert resp2.json()["user_id"] == resp1.json()["user_id"]


# ---------------------------------------------------------------------------
# POST /api/auth/google
# ---------------------------------------------------------------------------

FAKE_GOOGLE_CLAIMS = {"sub": "google-sub-001", "email": "user@gmail.com", "email_verified": True}


class TestGoogleAuth:
    @patch(
        "watersvc.routers.auth.verify_google_token",
        new_callable=AsyncMock,
        return_value=FAKE_GOOGLE_CLAIMS,
    )
    async def test_new_user(self, mock_verify, client):
        resp = await client.post(
            "/api/auth/google",
            json={"identity_token": "fake-google-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_new_user"] is True
        assert data["email"] == "user@gmail.com"

    @patch(
        "watersvc.routers.auth.verify_google_token",
        new_callable=AsyncMock,
        return_value=FAKE_GOOGLE_CLAIMS,
    )
    async def test_account_linking(self, mock_verify, client):
        anon_resp = await client.post(
            "/api/auth/anonymous", json={"device_id": "google-link-device"}
        )
        anon_token = anon_resp.json()["access_token"]
        anon_uid = anon_resp.json()["user_id"]

        resp = await client.post(
            "/api/auth/google",
            json={"identity_token": "fake-google-token"},
            headers={"Authorization": f"Bearer {anon_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["user_id"] == anon_uid
        assert resp.json()["email"] == "user@gmail.com"


# ---------------------------------------------------------------------------
# get_current_user dependency
# ---------------------------------------------------------------------------


class TestGetCurrentUser:
    async def test_valid_token(self, client, settings):
        # Get a real token via anonymous auth
        anon_resp = await client.post("/api/auth/anonymous", json={"device_id": "dep-test-device"})
        token = anon_resp.json()["access_token"]

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        user_id = await get_current_user(creds, _test_settings())
        assert user_id == anon_resp.json()["user_id"]

    async def test_expired_token(self):
        expired_settings = Settings(  # type: ignore[call-arg]
            mongodb_uri="mongodb://localhost:27017",
            jwt_secret=TEST_JWT_SECRET,
            jwt_expiry_hours=0,
        )
        token = create_access_token("user1", None, "anonymous", expired_settings)

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(creds, expired_settings)
        assert exc_info.value.status_code == 401

    async def test_invalid_token(self):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(creds, _test_settings())
        assert exc_info.value.status_code == 401
