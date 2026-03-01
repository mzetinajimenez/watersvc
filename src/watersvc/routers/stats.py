"""Water intake statistics API routes."""

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from watersvc.database.connection import get_database
from watersvc.database.service import WaterIntakeService
from watersvc.utils.schemas import (
    DailyBreakdown,
    DailyStatsResponse,
    IntakeResponse,
    PeriodStatsResponse,
)
from watersvc.utils.conversions import convert_from_oz
from watersvc.utils.timezone import get_date_n_days_ago, get_today_local

router = APIRouter()


async def get_user_preferences(db: AsyncIOMotorDatabase) -> tuple[str, float, str]:
    """
    Get user preferences from profile.

    Returns:
        Tuple of (timezone, daily_goal_oz, preferred_unit)
    """
    service = WaterIntakeService(db)
    profile = await service.get_profile()

    if not profile:
        # Return defaults if no profile exists
        return "UTC", 64.0, "oz"

    timezone = profile.get("preferences", {}).get("timezone", "UTC")
    daily_goal_oz = profile.get("daily_goal_oz", 64.0)
    preferred_unit = profile.get("preferences", {}).get("preferred_unit", "oz")

    return timezone, daily_goal_oz, preferred_unit


@router.get("/stats/daily", response_model=DailyStatsResponse)
async def get_daily_stats(
    date: str | None = Query(None, description="Date in YYYY-MM-DD format (default: today)"),
    unit: str | None = Query(
        None, description="Unit for display values (default: user preference)"
    ),
    include_entries: bool = Query(False, description="Include individual intake entries"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get daily water intake statistics.

    Returns total intake, progress toward goal, and optionally individual entries.
    """
    service = WaterIntakeService(db)

    # Get user preferences
    timezone, daily_goal_oz, preferred_unit = await get_user_preferences(db)

    # Use provided unit or user preference
    display_unit = unit if unit else preferred_unit

    # Use provided date or today in user's timezone
    target_date = date if date else get_today_local(timezone)

    # Aggregate daily total
    total_oz, entry_count = await service.aggregate_daily_total("default", target_date)

    # Calculate progress percentage
    progress_percent = (total_oz / daily_goal_oz * 100) if daily_goal_oz > 0 else 0.0

    # Convert to display units
    total_display = convert_from_oz(total_oz, display_unit)
    goal_display = convert_from_oz(daily_goal_oz, display_unit)

    # Get individual entries if requested
    entries = None
    if include_entries:
        intakes = await service.list_intakes(local_date=target_date, limit=500)
        entries = [
            IntakeResponse(
                id=str(intake["_id"]),
                **{k: v for k, v in intake.items() if k != "_id"},
            )
            for intake in intakes
        ]

    return DailyStatsResponse(
        date=target_date,
        total_oz=total_oz,
        total_display=round(total_display, 2),
        display_unit=display_unit,
        goal_oz=daily_goal_oz,
        goal_display=round(goal_display, 2),
        progress_percent=round(progress_percent, 2),
        entry_count=entry_count,
        entries=entries,
    )


@router.get("/stats/weekly", response_model=PeriodStatsResponse)
async def get_weekly_stats(
    date: str | None = Query(None, description="Reference date (default: today)"),
    unit: str | None = Query(
        None, description="Unit for display values (default: user preference)"
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get weekly water intake statistics (last 7 days).

    Returns aggregated stats and daily breakdown for the week.
    """
    service = WaterIntakeService(db)

    # Get user preferences
    timezone, daily_goal_oz, preferred_unit = await get_user_preferences(db)

    # Use provided unit or user preference
    display_unit = unit if unit else preferred_unit

    # Use provided date or today in user's timezone
    end_date = date if date else get_today_local(timezone)
    start_date = get_date_n_days_ago(end_date, 6)  # Last 7 days including today

    # Aggregate period stats
    daily_stats = await service.aggregate_period_stats("default", start_date, end_date)

    # Calculate totals and averages
    total_oz = sum(day["total_oz"] for day in daily_stats)
    total_days = 7
    daily_average_oz = total_oz / total_days if total_days > 0 else 0.0
    days_met_goal = sum(1 for day in daily_stats if day["total_oz"] >= daily_goal_oz)
    goal_completion_rate = (days_met_goal / total_days * 100) if total_days > 0 else 0.0

    # Convert to display units
    total_display = convert_from_oz(total_oz, display_unit)

    # Build daily breakdown (fill in missing days with 0)
    daily_breakdown = []
    for i in range(total_days):
        current_date = get_date_n_days_ago(end_date, total_days - 1 - i)
        day_stat = next((d for d in daily_stats if d["date"] == current_date), None)

        if day_stat:
            daily_breakdown.append(
                DailyBreakdown(
                    date=current_date,
                    total_oz=day_stat["total_oz"],
                    entry_count=day_stat["count"],
                    met_goal=day_stat["total_oz"] >= daily_goal_oz,
                )
            )
        else:
            daily_breakdown.append(
                DailyBreakdown(
                    date=current_date,
                    total_oz=0.0,
                    entry_count=0,
                    met_goal=False,
                )
            )

    return PeriodStatsResponse(
        period="weekly",
        start_date=start_date,
        end_date=end_date,
        total_oz=total_oz,
        total_display=round(total_display, 2),
        display_unit=display_unit,
        daily_average_oz=round(daily_average_oz, 2),
        days_met_goal=days_met_goal,
        total_days=total_days,
        goal_completion_rate=round(goal_completion_rate, 2),
        daily_breakdown=daily_breakdown,
    )


@router.get("/stats/monthly", response_model=PeriodStatsResponse)
async def get_monthly_stats(
    date: str | None = Query(None, description="Reference date (default: today)"),
    unit: str | None = Query(
        None, description="Unit for display values (default: user preference)"
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get monthly water intake statistics (last 30 days).

    Returns aggregated stats and daily breakdown for the month.
    """
    service = WaterIntakeService(db)

    # Get user preferences
    timezone, daily_goal_oz, preferred_unit = await get_user_preferences(db)

    # Use provided unit or user preference
    display_unit = unit if unit else preferred_unit

    # Use provided date or today in user's timezone
    end_date = date if date else get_today_local(timezone)
    start_date = get_date_n_days_ago(end_date, 29)  # Last 30 days including today

    # Aggregate period stats
    daily_stats = await service.aggregate_period_stats("default", start_date, end_date)

    # Calculate totals and averages
    total_oz = sum(day["total_oz"] for day in daily_stats)
    total_days = 30
    daily_average_oz = total_oz / total_days if total_days > 0 else 0.0
    days_met_goal = sum(1 for day in daily_stats if day["total_oz"] >= daily_goal_oz)
    goal_completion_rate = (days_met_goal / total_days * 100) if total_days > 0 else 0.0

    # Convert to display units
    total_display = convert_from_oz(total_oz, display_unit)

    # Build daily breakdown (fill in missing days with 0)
    daily_breakdown = []
    for i in range(total_days):
        current_date = get_date_n_days_ago(end_date, total_days - 1 - i)
        day_stat = next((d for d in daily_stats if d["date"] == current_date), None)

        if day_stat:
            daily_breakdown.append(
                DailyBreakdown(
                    date=current_date,
                    total_oz=day_stat["total_oz"],
                    entry_count=day_stat["count"],
                    met_goal=day_stat["total_oz"] >= daily_goal_oz,
                )
            )
        else:
            daily_breakdown.append(
                DailyBreakdown(
                    date=current_date,
                    total_oz=0.0,
                    entry_count=0,
                    met_goal=False,
                )
            )

    return PeriodStatsResponse(
        period="monthly",
        start_date=start_date,
        end_date=end_date,
        total_oz=total_oz,
        total_display=round(total_display, 2),
        display_unit=display_unit,
        daily_average_oz=round(daily_average_oz, 2),
        days_met_goal=days_met_goal,
        total_days=total_days,
        goal_completion_rate=round(goal_completion_rate, 2),
        daily_breakdown=daily_breakdown,
    )
