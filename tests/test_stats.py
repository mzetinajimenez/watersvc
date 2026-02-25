"""Integration tests for stats API routes."""

import pytest


async def test_daily_stats_no_intakes(client):
    response = await client.get("/api/stats/daily?date=2024-01-15")
    assert response.status_code == 200
    data = response.json()
    assert data["total_oz"] == 0.0
    assert data["progress_percent"] == 0.0
    assert data["entry_count"] == 0


async def test_daily_stats_with_intakes(client):
    await client.post(
        "/api/intakes",
        json={"amount": 16.0, "unit": "oz", "timestamp": "2024-01-15T10:00:00Z"},
    )
    await client.post(
        "/api/intakes",
        json={"amount": 24.0, "unit": "oz", "timestamp": "2024-01-15T14:00:00Z"},
    )
    response = await client.get("/api/stats/daily?date=2024-01-15")
    assert response.status_code == 200
    data = response.json()
    assert data["total_oz"] == pytest.approx(40.0)
    assert data["entry_count"] == 2
    assert data["progress_percent"] > 0


async def test_daily_stats_with_date_param(client):
    await client.post(
        "/api/intakes",
        json={"amount": 8.0, "unit": "oz", "timestamp": "2024-01-15T10:00:00Z"},
    )
    await client.post(
        "/api/intakes",
        json={"amount": 12.0, "unit": "oz", "timestamp": "2024-01-16T10:00:00Z"},
    )
    response = await client.get("/api/stats/daily?date=2024-01-15")
    data = response.json()
    assert data["total_oz"] == pytest.approx(8.0)
    assert data["entry_count"] == 1


async def test_weekly_stats(client):
    response = await client.get("/api/stats/weekly?date=2024-01-15")
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "weekly"
    assert "daily_breakdown" in data
    assert len(data["daily_breakdown"]) == 7


async def test_monthly_stats(client):
    response = await client.get("/api/stats/monthly?date=2024-01-31")
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "monthly"
    assert "daily_breakdown" in data
    assert len(data["daily_breakdown"]) == 30
