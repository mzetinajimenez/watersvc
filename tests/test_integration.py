"""Integration test against real MongoDB Atlas."""

import pytest


@pytest.mark.integration
async def test_full_lifecycle(integration_client):
    """Create profile → update it → add intake → delete intake."""
    client = integration_client

    # 1. Initialize profile
    resp = await client.post(
        "/api/profile/initialize",
        json={
            "username": "integration_testuser",
            "email": "integration@test.com",
            "daily_goal_oz": 64.0,
            "preferred_unit": "oz",
            "timezone": "UTC",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["username"] == "integration_testuser"

    # 2. Update profile
    resp = await client.patch("/api/profile", json={"username": "integration_updated"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "integration_updated"

    # 3. Add intake
    resp = await client.post(
        "/api/intakes",
        json={"amount": 16.0, "unit": "oz", "notes": "integration test entry"},
    )
    assert resp.status_code == 201
    intake_id = resp.json()["id"]
    assert resp.json()["amount_oz"] == 16.0

    # 4. Verify intake is retrievable
    resp = await client.get(f"/api/intakes/{intake_id}")
    assert resp.status_code == 200
    assert resp.json()["notes"] == "integration test entry"

    # 5. Delete intake
    resp = await client.delete(f"/api/intakes/{intake_id}")
    assert resp.status_code == 204

    # 6. Confirm deletion
    resp = await client.get(f"/api/intakes/{intake_id}")
    assert resp.status_code == 404
