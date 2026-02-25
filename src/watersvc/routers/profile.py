"""Profile management API routes."""

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from watersvc.database.connection import get_database
from watersvc.database.service import WaterIntakeService
from watersvc.models.documents import UserPreferences, UserProfileDocument
from watersvc.models.requests import InitializeProfileRequest, UpdateProfileRequest
from watersvc.models.responses import ProfileResponse

router = APIRouter()


@router.post("/profile/initialize", response_model=ProfileResponse, status_code=201)
async def initialize_profile(
    request: InitializeProfileRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Initialize user profile (one-time setup).

    Creates a new user profile with the provided information.
    Only one profile is allowed for the single-user app.
    """
    service = WaterIntakeService(db)

    # Check if profile already exists
    existing_profile = await service.get_profile()
    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Profile already exists. Use PATCH /profile to update.",
        )

    # Create profile document
    profile_data = UserProfileDocument(
        username=request.username,
        email=request.email,
        daily_goal_oz=request.daily_goal_oz,
        preferences=UserPreferences(
            preferred_unit=request.preferred_unit,
            timezone=request.timezone,
        ),
    )

    # Insert into database
    created_profile = await service.create_profile(profile_data.model_dump())

    return ProfileResponse(**created_profile)


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Get current user profile."""
    service = WaterIntakeService(db)

    profile = await service.get_profile()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found. Use POST /profile/initialize to create.",
        )

    return ProfileResponse(**profile)


@router.put("/profile", response_model=ProfileResponse)
async def update_profile_full(
    request: InitializeProfileRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Update user profile (full update).

    Replaces all profile fields with the provided data.
    """
    service = WaterIntakeService(db)

    # Check if profile exists
    existing_profile = await service.get_profile()
    if not existing_profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found. Use POST /profile/initialize to create.",
        )

    # Update profile
    update_data = {
        "username": request.username,
        "email": request.email,
        "daily_goal_oz": request.daily_goal_oz,
        "preferences": UserPreferences(
            preferred_unit=request.preferred_unit,
            timezone=request.timezone,
        ).model_dump(),
    }

    updated_profile = await service.update_profile("default", update_data)
    if not updated_profile:
        raise HTTPException(status_code=500, detail="Failed to update profile")

    return ProfileResponse(**updated_profile)


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile_partial(
    request: UpdateProfileRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Update user profile (partial update).

    Updates only the provided fields, leaving others unchanged.
    """
    service = WaterIntakeService(db)

    # Check if profile exists
    existing_profile = await service.get_profile()
    if not existing_profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found. Use POST /profile/initialize to create.",
        )

    # Build update data with only provided fields
    update_data: dict[str, object] = {}
    if request.username is not None:
        update_data["username"] = request.username
    if request.email is not None:
        update_data["email"] = request.email
    if request.daily_goal_oz is not None:
        update_data["daily_goal_oz"] = request.daily_goal_oz
    if request.preferences is not None:
        update_data["preferences"] = request.preferences.model_dump()

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    updated_profile = await service.update_profile("default", update_data)
    if not updated_profile:
        raise HTTPException(status_code=500, detail="Failed to update profile")

    return ProfileResponse(**updated_profile)
