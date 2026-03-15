"""Tests for timezone utilities."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from watersvc.utils.timezone import (
    get_date_n_days_ago,
    get_date_range_utc,
    get_local_date_time,
    get_today_local,
)


class TestGetLocalDateTime:
    """Tests for converting UTC datetime to local date and time."""

    def test_utc_to_utc(self):
        """Test UTC to UTC conversion (identity)."""
        dt = datetime(2026, 1, 12, 14, 30, 0, tzinfo=ZoneInfo("UTC"))
        local_date, local_time = get_local_date_time(dt, "UTC")
        assert local_date == "2026-01-12"
        assert local_time == "14:30:00"

    def test_utc_to_eastern(self):
        """Test UTC to US Eastern conversion."""
        dt = datetime(2026, 1, 12, 20, 0, 0, tzinfo=ZoneInfo("UTC"))
        local_date, local_time = get_local_date_time(dt, "America/New_York")
        # UTC 20:00 -> EST 15:00 (EST is UTC-5)
        assert local_date == "2026-01-12"
        assert local_time == "15:00:00"

    def test_utc_to_pacific(self):
        """Test UTC to US Pacific conversion."""
        dt = datetime(2026, 1, 12, 20, 0, 0, tzinfo=ZoneInfo("UTC"))
        local_date, local_time = get_local_date_time(dt, "America/Los_Angeles")
        # UTC 20:00 -> PST 12:00 (PST is UTC-8)
        assert local_date == "2026-01-12"
        assert local_time == "12:00:00"

    def test_date_rollover(self):
        """Test date changes across timezone boundaries."""
        # UTC 2:00 AM on Jan 13 -> Jan 12 at 9:00 PM EST
        dt = datetime(2026, 1, 13, 2, 0, 0, tzinfo=ZoneInfo("UTC"))
        local_date, local_time = get_local_date_time(dt, "America/New_York")
        assert local_date == "2026-01-12"
        assert local_time == "21:00:00"

    def test_naive_datetime_assumed_utc(self):
        """Test that naive datetime is assumed to be UTC."""
        dt = datetime(2026, 1, 12, 14, 30, 0)
        local_date, local_time = get_local_date_time(dt, "America/New_York")
        assert local_date == "2026-01-12"
        assert local_time == "09:30:00"


class TestGetDateRangeUTC:
    """Tests for getting UTC range from local date."""

    def test_utc_date_range(self):
        """Test getting UTC range for a UTC date."""
        start, end = get_date_range_utc("2026-01-12", "UTC")
        assert start == datetime(2026, 1, 12, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert end == datetime(2026, 1, 12, 23, 59, 59, 999999, tzinfo=ZoneInfo("UTC"))

    def test_eastern_date_range(self):
        """Test getting UTC range for an Eastern date."""
        start, end = get_date_range_utc("2026-01-12", "America/New_York")
        # Jan 12 00:00 EST = Jan 12 05:00 UTC
        # Jan 12 23:59 EST = Jan 13 04:59 UTC
        assert start.day == 12
        assert start.hour == 5  # EST is UTC-5 in winter
        assert end.day == 13
        assert end.hour == 4

    def test_pacific_date_range(self):
        """Test getting UTC range for a Pacific date."""
        start, end = get_date_range_utc("2026-01-12", "America/Los_Angeles")
        # Jan 12 00:00 PST = Jan 12 08:00 UTC
        # Jan 12 23:59 PST = Jan 13 07:59 UTC
        assert start.day == 12
        assert start.hour == 8  # PST is UTC-8 in winter
        assert end.day == 13
        assert end.hour == 7

    def test_invalid_date_format(self):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError):
            get_date_range_utc("01/12/2026", "UTC")

    def test_date_range_spans_24_hours(self):
        """Test that the range covers exactly 24 hours."""
        start, end = get_date_range_utc("2026-01-12", "UTC")
        duration = end - start
        # Should be 23:59:59.999999, very close to 24 hours
        assert duration.days == 0
        assert duration.seconds == 86399  # 23:59:59


class TestGetTodayLocal:
    """Tests for getting today's date in local timezone."""

    def test_get_today_utc(self):
        """Test getting today in UTC."""
        today = get_today_local("UTC")
        assert isinstance(today, str)
        assert len(today) == 10  # YYYY-MM-DD format
        assert today.count("-") == 2

    def test_get_today_eastern(self):
        """Test getting today in Eastern timezone."""
        today = get_today_local("America/New_York")
        assert isinstance(today, str)
        assert len(today) == 10

    def test_date_format(self):
        """Test that returned date is in correct format."""
        today = get_today_local("UTC")
        # Should parse without error
        datetime.strptime(today, "%Y-%m-%d")


class TestGetDateNDaysAgo:
    """Tests for getting past dates."""

    def test_one_day_ago(self):
        """Test getting yesterday's date."""
        result = get_date_n_days_ago("2026-01-12", 1)
        assert result == "2026-01-11"

    def test_seven_days_ago(self):
        """Test getting date 7 days ago."""
        result = get_date_n_days_ago("2026-01-12", 7)
        assert result == "2026-01-05"

    def test_thirty_days_ago(self):
        """Test getting date 30 days ago."""
        result = get_date_n_days_ago("2026-01-31", 30)
        assert result == "2026-01-01"

    def test_across_month_boundary(self):
        """Test date calculation across month boundary."""
        result = get_date_n_days_ago("2026-02-05", 10)
        assert result == "2026-01-26"

    def test_across_year_boundary(self):
        """Test date calculation across year boundary."""
        result = get_date_n_days_ago("2026-01-05", 10)
        assert result == "2025-12-26"

    def test_zero_days_ago(self):
        """Test with zero days (should return same date)."""
        result = get_date_n_days_ago("2026-01-12", 0)
        assert result == "2026-01-12"

    def test_invalid_date_format(self):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError):
            get_date_n_days_ago("01/12/2026", 7)


class TestDSTTransitions:
    """Tests for daylight saving time transitions."""

    def test_spring_forward(self):
        """Test DST spring forward transition."""
        # In 2026, DST starts on March 8 at 2:00 AM (skips to 3:00 AM)
        # This is just before the transition
        dt = datetime(2026, 3, 8, 6, 30, 0, tzinfo=ZoneInfo("UTC"))
        local_date, local_time = get_local_date_time(dt, "America/New_York")
        # UTC 6:30 AM = EST 1:30 AM (before DST)
        assert local_date == "2026-03-08"

    def test_fall_back(self):
        """Test DST fall back transition."""
        # In 2026, DST ends on November 1 at 2:00 AM (falls back to 1:00 AM)
        dt = datetime(2026, 11, 1, 7, 30, 0, tzinfo=ZoneInfo("UTC"))
        local_date, local_time = get_local_date_time(dt, "America/New_York")
        assert local_date == "2026-11-01"


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_leap_year_date(self):
        """Test handling of leap year dates."""
        # 2024 is a leap year
        result = get_date_n_days_ago("2024-03-01", 1)
        assert result == "2024-02-29"

    def test_non_leap_year(self):
        """Test handling of non-leap year."""
        # 2026 is not a leap year
        result = get_date_n_days_ago("2026-03-01", 1)
        assert result == "2026-02-28"

    def test_end_of_year_date(self):
        """Test handling of end-of-year date."""
        result = get_date_n_days_ago("2026-12-31", 0)
        assert result == "2026-12-31"
