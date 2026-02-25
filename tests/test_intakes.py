"""Integration tests for intakes API routes."""

import pytest


async def test_create_intake_oz(client):
    response = await client.post("/api/intakes", json={"amount": 16.0, "unit": "oz"})
    assert response.status_code == 201
    data = response.json()
    assert data["amount_oz"] == pytest.approx(16.0)
    assert data["original_amount"] == 16.0
    assert data["original_unit"] == "oz"
    assert "id" in data


async def test_create_intake_ml(client):
    response = await client.post("/api/intakes", json={"amount": 300.0, "unit": "ml"})
    assert response.status_code == 201
    data = response.json()
    # 300 ml * 0.033814 oz/ml
    assert data["amount_oz"] == pytest.approx(300 * 0.033814, rel=1e-3)
    assert data["original_unit"] == "ml"


async def test_list_intakes_empty(client):
    response = await client.get("/api/intakes")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_intakes(client):
    await client.post("/api/intakes", json={"amount": 8.0, "unit": "oz"})
    await client.post("/api/intakes", json={"amount": 12.0, "unit": "oz"})
    response = await client.get("/api/intakes")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_intakes_filter_by_date(client):
    await client.post(
        "/api/intakes",
        json={"amount": 8.0, "unit": "oz", "timestamp": "2024-01-15T10:00:00Z"},
    )
    await client.post(
        "/api/intakes",
        json={"amount": 12.0, "unit": "oz", "timestamp": "2024-01-16T10:00:00Z"},
    )
    response = await client.get("/api/intakes?date=2024-01-15")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["local_date"] == "2024-01-15"


async def test_get_intake_by_id(client):
    create_resp = await client.post("/api/intakes", json={"amount": 8.0, "unit": "oz"})
    intake_id = create_resp.json()["id"]
    response = await client.get(f"/api/intakes/{intake_id}")
    assert response.status_code == 200
    assert response.json()["id"] == intake_id


async def test_get_intake_not_found(client):
    response = await client.get("/api/intakes/000000000000000000000001")
    assert response.status_code == 404


async def test_get_intake_invalid_id(client):
    response = await client.get("/api/intakes/not-an-objectid")
    assert response.status_code == 400


async def test_put_intake(client):
    create_resp = await client.post("/api/intakes", json={"amount": 8.0, "unit": "oz"})
    intake_id = create_resp.json()["id"]
    response = await client.put(
        f"/api/intakes/{intake_id}",
        json={"amount": 16.0, "unit": "oz"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount_oz"] == pytest.approx(16.0)
    assert data["original_amount"] == 16.0


async def test_patch_intake(client):
    create_resp = await client.post(
        "/api/intakes", json={"amount": 8.0, "unit": "oz", "notes": "morning"}
    )
    intake_id = create_resp.json()["id"]
    response = await client.patch(
        f"/api/intakes/{intake_id}",
        json={"notes": "updated note"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "updated note"
    assert data["amount_oz"] == pytest.approx(8.0)  # unchanged


async def test_delete_intake(client):
    create_resp = await client.post("/api/intakes", json={"amount": 8.0, "unit": "oz"})
    intake_id = create_resp.json()["id"]
    delete_resp = await client.delete(f"/api/intakes/{intake_id}")
    assert delete_resp.status_code == 204
    get_resp = await client.get(f"/api/intakes/{intake_id}")
    assert get_resp.status_code == 404
