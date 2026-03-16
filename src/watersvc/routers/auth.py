"""Authentication API routes."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from watersvc.auth.jwt import create_access_token, decode_access_token
from watersvc.auth.providers import verify_apple_token, verify_google_token
from watersvc.config import Settings, get_settings
from watersvc.database.connection import get_database
from watersvc.database.service import WaterIntakeService
from watersvc.utils.schemas import AnonymousAuthRequest, AuthResponse, ProviderAuthRequest

router = APIRouter()


def _new_user_id() -> str:
    return uuid.uuid4().hex


def _extract_bearer_token(request: Request) -> str | None:
    """Extract Bearer token from Authorization header, if present."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:]
    return None


@router.post("/auth/anonymous", response_model=AuthResponse)
async def anonymous_auth(
    body: AnonymousAuthRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    """Authenticate or register via device ID (anonymous)."""
    service = WaterIntakeService(db)

    existing = await service.find_user_by_provider("anonymous", body.device_id)
    if existing:
        token = create_access_token(
            existing["user_id"], existing.get("email"), "anonymous", settings
        )
        return AuthResponse(
            access_token=token,
            user_id=existing["user_id"],
            email=existing.get("email"),
            is_new_user=False,
        )

    user_id = _new_user_id()
    now = datetime.now(tz=timezone.utc)
    user_doc = {
        "user_id": user_id,
        "providers": [{"provider": "anonymous", "provider_id": body.device_id}],
        "email": None,
        "created_at": now,
        "updated_at": now,
    }
    await service.create_user(user_doc)

    token = create_access_token(user_id, None, "anonymous", settings)
    return AuthResponse(access_token=token, user_id=user_id, is_new_user=True)


async def _provider_auth(
    provider_name: str,
    body: ProviderAuthRequest,
    request: Request,
    db: AsyncIOMotorDatabase,
    settings: Settings,
    verify_fn,
) -> AuthResponse:
    """Shared logic for Apple / Google provider authentication."""
    claims = await verify_fn(body.identity_token, settings)
    provider_sub = claims["sub"]
    email = claims.get("email") or body.email

    service = WaterIntakeService(db)

    # Check if this provider identity is already linked to a user
    existing = await service.find_user_by_provider(provider_name, provider_sub)
    if existing:
        # Returning user
        token = create_access_token(
            existing["user_id"], existing.get("email"), provider_name, settings
        )
        return AuthResponse(
            access_token=token,
            user_id=existing["user_id"],
            email=existing.get("email"),
            is_new_user=False,
        )

    # Not found — check for optional Bearer token (account linking)
    bearer = _extract_bearer_token(request)
    if bearer:
        try:
            payload = decode_access_token(bearer, settings)
            anon_user_id = payload["sub"]
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token for account linking",
            ) from err

        # Verify the anonymous user exists
        anon_user = await service.users.find_one({"user_id": anon_user_id})
        if not anon_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User from bearer token not found",
            )

        # Link provider to existing anonymous account
        provider_entry = {"provider": provider_name, "provider_id": provider_sub}
        updated = await service.add_provider_to_user(anon_user_id, provider_entry, email)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This account is already linked to another user",
            )

        token = create_access_token(anon_user_id, email, provider_name, settings)
        return AuthResponse(
            access_token=token,
            user_id=anon_user_id,
            email=email,
            is_new_user=False,
        )

    # No existing link, no bearer — create brand new user with this provider
    user_id = _new_user_id()
    now = datetime.now(tz=timezone.utc)
    user_doc = {
        "user_id": user_id,
        "providers": [{"provider": provider_name, "provider_id": provider_sub}],
        "email": email,
        "created_at": now,
        "updated_at": now,
    }
    await service.create_user(user_doc)

    token = create_access_token(user_id, email, provider_name, settings)
    return AuthResponse(access_token=token, user_id=user_id, email=email, is_new_user=True)


@router.post("/auth/apple", response_model=AuthResponse)
async def apple_auth(
    body: ProviderAuthRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    """Authenticate or link via Sign in with Apple."""
    return await _provider_auth("apple", body, request, db, settings, verify_apple_token)


@router.post("/auth/google", response_model=AuthResponse)
async def google_auth(
    body: ProviderAuthRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    """Authenticate or link via Sign in with Google."""
    return await _provider_auth("google", body, request, db, settings, verify_google_token)
