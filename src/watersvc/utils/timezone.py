"""Timezone handling utilities for accurate date/time calculations."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def get_local_date_time(dt: datetime, timezone: str) -> tuple[str, str]:
    """
    Convert UTC datetime to local date and time strings.

    Args:
        dt: The datetime to convert (assumed to be UTC)
        timezone: IANA timezone string (e.g., "America/New_York")

    Returns:
        Tuple of (local_date, local_time) where:
        - local_date is "YYYY-MM-DD" format
        - local_time is "HH:MM:SS" format

    Raises:
        ZoneInfoNotFoundError: If the timezone is invalid
    """
    # Ensure datetime is UTC-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    # Convert to local timezone
    local_tz = ZoneInfo(timezone)
    local_dt = dt.astimezone(local_tz)

    return (
        local_dt.strftime("%Y-%m-%d"),
        local_dt.strftime("%H:%M:%S"),
    )


def get_date_range_utc(date_str: str, timezone: str) -> tuple[datetime, datetime]:
    """
    Get UTC start and end datetime for a local date.

    This function takes a date string and timezone, and returns the UTC datetime
    range that covers the entire day in that timezone. This is useful for querying
    database entries that fall within a specific local date.

    Args:
        date_str: Date string in "YYYY-MM-DD" format
        timezone: IANA timezone string (e.g., "America/New_York")

    Returns:
        Tuple of (start_utc, end_utc) covering the entire local day

    Raises:
        ValueError: If the date string is not in the correct format
        ZoneInfoNotFoundError: If the timezone is invalid
    """
    local_tz = ZoneInfo(timezone)

    # Parse the date string
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    # Create start and end of day in local timezone
    start_local = date_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=local_tz)
    end_local = date_obj.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=local_tz)

    # Convert to UTC
    utc_tz = ZoneInfo("UTC")
    start_utc = start_local.astimezone(utc_tz)
    end_utc = end_local.astimezone(utc_tz)

    return start_utc, end_utc


def get_today_local(timezone: str) -> str:
    """
    Get today's date in the specified timezone.

    Args:
        timezone: IANA timezone string (e.g., "America/New_York")

    Returns:
        Today's date in "YYYY-MM-DD" format in the specified timezone

    Raises:
        ZoneInfoNotFoundError: If the timezone is invalid
    """
    local_tz = ZoneInfo(timezone)
    now_local = datetime.now(local_tz)
    return now_local.strftime("%Y-%m-%d")


def get_date_n_days_ago(date_str: str, n_days: int) -> str:
    """
    Get the date that is n days before the given date.

    Args:
        date_str: Date string in "YYYY-MM-DD" format
        n_days: Number of days to go back

    Returns:
        Date string in "YYYY-MM-DD" format

    Raises:
        ValueError: If the date string is not in the correct format
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    past_date = date_obj - timedelta(days=n_days)
    return past_date.strftime("%Y-%m-%d")
