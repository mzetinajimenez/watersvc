"""Pydantic models for API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from watersvc.models.documents import UserPreferences


class ProfileResponse(BaseModel):
    """Response model for user profile."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    username: str
    email: str
    daily_goal_oz: float
    preferences: UserPreferences
    created_at: datetime
    updated_at: datetime


class IntakeResponse(BaseModel):
    """Response model for water intake entry."""

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
    """Response model for daily statistics."""

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
    """Daily breakdown for period statistics."""

    date: str
    total_oz: float
    entry_count: int
    met_goal: bool


class PeriodStatsResponse(BaseModel):
    """Response model for weekly/monthly statistics."""

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
