"""Pydantic models for API request validation."""

from datetime import datetime

from pydantic import BaseModel, Field

from watersvc.models.documents import UserPreferences


class InitializeProfileRequest(BaseModel):
    """Request model for initializing user profile."""

    username: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    daily_goal_oz: float = Field(default=64.0, gt=0, le=1000)
    preferred_unit: str = Field(default="oz", pattern="^(oz|ml|l|cups)$")
    timezone: str = Field(default="UTC")


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile (all fields optional)."""

    username: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    daily_goal_oz: float | None = Field(default=None, gt=0, le=1000)
    preferences: UserPreferences | None = None


class CreateIntakeRequest(BaseModel):
    """Request model for creating a water intake entry."""

    amount: float = Field(gt=0, le=500)
    unit: str = Field(pattern="^(oz|ml|l|cups)$")
    timestamp: datetime | None = None
    notes: str | None = Field(default=None, max_length=500)


class UpdateIntakeRequest(BaseModel):
    """Request model for updating a water intake entry (all fields optional)."""

    amount: float | None = Field(default=None, gt=0, le=500)
    unit: str | None = Field(default=None, pattern="^(oz|ml|l|cups)$")
    timestamp: datetime | None = None
    notes: str | None = Field(default=None, max_length=500)
