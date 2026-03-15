"""Profile management API routes."""

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from watersvc.database.connection import get_database
from watersvc.database.service import WaterIntakeService
from watersvc.utils.schemas import (
    InitializeProfileRequest,
    ProfileResponse,
    UpdateProfileRequest,
    UserPreferences,
    UserProfileDocument,
)

router = APIRouter()


@router.post("/profile", response_model=ProfileResponse, status_code=201)
async def create_profile(
    request: InitializeProfileRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Create a new user profile."""
    service = WaterIntakeService(db)

    existing_profile = await service.get_profile(request.user_id)
    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Profile already exists. Use PATCH /profile/{user_id} to update.",
        )

    profile_data = UserProfileDocument(
        user_id=request.user_id,
        username=request.username,
        email=request.email,
        daily_goal_oz=request.daily_goal_oz,
        preferences=UserPreferences(
            preferred_unit=request.preferred_unit,
            timezone=request.timezone,
        ),
    )

    created_profile = await service.create_profile(profile_data.model_dump())

    return ProfileResponse(**created_profile)


@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Get user profile."""
    service = WaterIntakeService(db)

    profile = await service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return ProfileResponse(**profile)


@router.patch("/profile/{user_id}", response_model=ProfileResponse)
async def update_profile_partial(
    user_id: str,
    request: UpdateProfileRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Update user profile (partial update)."""
    service = WaterIntakeService(db)

    existing_profile = await service.get_profile(user_id)
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

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

    updated_profile = await service.update_profile(user_id, update_data)
    if not updated_profile:
        raise HTTPException(status_code=500, detail="Failed to update profile")

    return ProfileResponse(**updated_profile)


@router.delete("/profile/{user_id}", status_code=204)
async def delete_profile(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Delete user profile."""
    service = WaterIntakeService(db)

    deleted = await service.delete_profile(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return None
