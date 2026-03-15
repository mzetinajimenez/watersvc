"""Integration tests for intakes API routes."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

USER_ID = "testuser"
BASE = f"?user_id={USER_ID}"


async def test_create_intake_oz(client):
    response = await client.post(f"/api/intakes{BASE}", json={"amount": 16.0, "unit": "oz"})
    assert response.status_code == 201
    data = response.json()
    assert data["amount_oz"] == pytest.approx(16.0)
    assert data["original_amount"] == 16.0
    assert data["original_unit"] == "oz"
    assert "id" in data


async def test_create_intake_ml(client):
    response = await client.post(f"/api/intakes{BASE}", json={"amount": 300.0, "unit": "ml"})
    assert response.status_code == 201
    data = response.json()
    # 300 ml / 29.5735295625 ml per oz (exact SI)
    assert data["amount_oz"] == pytest.approx(300 / 29.5735295625, rel=1e-3)
    assert data["original_unit"] == "ml"


async def test_list_intakes_empty(client):
    response = await client.get(f"/api/intakes{BASE}")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_intakes(client):
    await client.post(f"/api/intakes{BASE}", json={"amount": 8.0, "unit": "oz"})
    await client.post(f"/api/intakes{BASE}", json={"amount": 12.0, "unit": "oz"})
    response = await client.get(f"/api/intakes{BASE}")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_intakes_filter_by_date(client):
    with patch("watersvc.routers.intakes.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        await client.post(f"/api/intakes{BASE}", json={"amount": 8.0, "unit": "oz"})

        mock_dt.now.return_value = datetime(2024, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
        await client.post(f"/api/intakes{BASE}", json={"amount": 12.0, "unit": "oz"})

    response = await client.get(f"/api/intakes{BASE}&date=2024-01-15")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["local_date"] == "2024-01-15"


async def test_get_intake_by_id(client):
    create_resp = await client.post(f"/api/intakes{BASE}", json={"amount": 8.0, "unit": "oz"})
    intake_id = create_resp.json()["id"]
    response = await client.get(f"/api/intakes/{intake_id}{BASE}")
    assert response.status_code == 200
    assert response.json()["id"] == intake_id


async def test_get_intake_not_found(client):
    response = await client.get(f"/api/intakes/000000000000000000000001{BASE}")
    assert response.status_code == 404


async def test_get_intake_invalid_id(client):
    response = await client.get(f"/api/intakes/not-an-objectid{BASE}")
    assert response.status_code == 400


async def test_patch_intake_full(client):
    create_resp = await client.post(f"/api/intakes{BASE}", json={"amount": 8.0, "unit": "oz"})
    intake_id = create_resp.json()["id"]
    response = await client.patch(
        f"/api/intakes/{intake_id}{BASE}",
        json={"amount": 16.0, "unit": "oz"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount_oz"] == pytest.approx(16.0)
    assert data["original_amount"] == 16.0


async def test_patch_intake(client):
    create_resp = await client.post(
        f"/api/intakes{BASE}", json={"amount": 8.0, "unit": "oz", "notes": "morning"}
    )
    intake_id = create_resp.json()["id"]
    response = await client.patch(
        f"/api/intakes/{intake_id}{BASE}",
        json={"notes": "updated note"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "updated note"
    assert data["amount_oz"] == pytest.approx(8.0)  # unchanged


async def test_delete_intake(client):
    create_resp = await client.post(f"/api/intakes{BASE}", json={"amount": 8.0, "unit": "oz"})
    intake_id = create_resp.json()["id"]
    delete_resp = await client.delete(f"/api/intakes/{intake_id}{BASE}")
    assert delete_resp.status_code == 204
    get_resp = await client.get(f"/api/intakes/{intake_id}{BASE}")
    assert get_resp.status_code == 404
