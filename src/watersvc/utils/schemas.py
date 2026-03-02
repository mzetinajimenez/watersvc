"""Pydantic schemas for documents, requests, and responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Unit = Literal["oz", "ml", "l", "cups"]

# --- Shared ---


class UserPreferences(BaseModel):
    preferred_unit: Unit = "oz"
    timezone: str = "UTC"
    reminder_enabled: bool = False
    reminder_times: list[str] = Field(default_factory=list)


# --- Documents (MongoDB shapes) ---


class UserProfileDocument(BaseModel):
    user_id: str
    username: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    daily_goal_oz: float = Field(gt=0, le=1000)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WaterIntakeDocument(BaseModel):
    user_id: str
    amount_oz: float = Field(gt=0, le=500)
    original_amount: float = Field(gt=0, le=500)
    original_unit: Unit
    timestamp: datetime
    local_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    local_time: str = Field(pattern=r"^\d{2}:\d{2}:\d{2}$")
    timezone: str
    notes: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Requests ---


class InitializeProfileRequest(BaseModel):
    user_id: str
    username: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    daily_goal_oz: float = Field(default=64.0, gt=0, le=1000)
    preferred_unit: Unit = "oz"
    timezone: str = "UTC"


class UpdateProfileRequest(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    daily_goal_oz: float | None = Field(default=None, gt=0, le=1000)
    preferences: UserPreferences | None = None


class CreateIntakeRequest(BaseModel):
    amount: float = Field(gt=0, le=500)
    unit: Unit
    notes: str | None = Field(default=None, max_length=500)


class UpdateIntakeRequest(BaseModel):
    amount: float | None = Field(default=None, gt=0, le=500)
    unit: Unit | None = None
    notes: str | None = Field(default=None, max_length=500)


# --- Responses ---


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    username: str
    email: str
    daily_goal_oz: float
    preferences: UserPreferences
    created_at: datetime
    updated_at: datetime


class IntakeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    amount_oz: float
    original_amount: float
    original_unit: str
    timestamp: datetime
    local_date: str
    local_time: str
    timezone: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class DailyStatsResponse(BaseModel):
    date: str
    total_oz: float
    total_display: float
    display_unit: str
    goal_oz: float
    goal_display: float
    progress_percent: float
    entry_count: int
    entries: list[IntakeResponse] | None = None


class DailyBreakdown(BaseModel):
    date: str
    total_oz: float
    entry_count: int
    met_goal: bool


class PeriodStatsResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    total_oz: float
    total_display: float
    display_unit: str
    daily_average_oz: float
    days_met_goal: int
    total_days: int
    goal_completion_rate: float
    daily_breakdown: list[DailyBreakdown]
