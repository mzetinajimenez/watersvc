"""Pydantic models for MongoDB documents."""

from datetime import datetime

from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    """User preferences for water tracking."""

    preferred_unit: str = Field(default="oz", pattern="^(oz|ml|l|cups)$")
    timezone: str = Field(default="UTC")
    reminder_enabled: bool = Field(default=False)
    reminder_times: list[str] = Field(default_factory=list)


class UserProfileDocument(BaseModel):
    """MongoDB document schema for user profile."""

    user_id: str = Field(default="default")
    username: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    daily_goal_oz: float = Field(gt=0, le=1000)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WaterIntakeDocument(BaseModel):
    """MongoDB document schema for water intake entry."""

    user_id: str = Field(default="default")
    amount_oz: float = Field(gt=0, le=500)
    original_amount: float = Field(gt=0, le=500)
    original_unit: str = Field(pattern="^(oz|ml|l|cups)$")
    timestamp: datetime
    local_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    local_time: str = Field(pattern=r"^\d{2}:\d{2}:\d{2}$")
    timezone: str
    notes: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
