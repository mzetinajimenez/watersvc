"""Integration tests for profile API routes."""

PROFILE_PAYLOAD = {
    "user_id": "testuser",
    "username": "testuser",
    "email": "test@example.com",
    "daily_goal_oz": 64.0,
    "preferred_unit": "oz",
    "timezone": "UTC",
}


async def test_create_profile(client):
    response = await client.post("/api/profile", json=PROFILE_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["daily_goal_oz"] == 64.0
    assert data["user_id"] == "testuser"
    assert "created_at" in data


async def test_create_profile_duplicate(client):
    await client.post("/api/profile", json=PROFILE_PAYLOAD)
    response = await client.post("/api/profile", json=PROFILE_PAYLOAD)
    assert response.status_code == 400


async def test_get_profile_not_found(client):
    response = await client.get("/api/profile/testuser")
    assert response.status_code == 404


async def test_get_profile(client):
    await client.post("/api/profile", json=PROFILE_PAYLOAD)
    response = await client.get("/api/profile/testuser")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


async def test_patch_profile_full(client):
    await client.post("/api/profile", json=PROFILE_PAYLOAD)
    response = await client.patch(
        "/api/profile/testuser",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "daily_goal_oz": 80.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert data["daily_goal_oz"] == 80.0


async def test_patch_profile(client):
    await client.post("/api/profile", json=PROFILE_PAYLOAD)
    response = await client.patch("/api/profile/testuser", json={"username": "patcheduser"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "patcheduser"
    assert data["email"] == "test@example.com"  # unchanged


async def test_patch_profile_empty_body(client):
    await client.post("/api/profile", json=PROFILE_PAYLOAD)
    response = await client.patch("/api/profile/testuser", json={})
    assert response.status_code == 400


async def test_delete_profile_success(client):
    await client.post("/api/profile", json=PROFILE_PAYLOAD)
    response = await client.delete("/api/profile/testuser")
    assert response.status_code == 204


async def test_delete_profile_not_found(client):
    response = await client.delete("/api/profile/testuser")
    assert response.status_code == 404


async def test_delete_profile_then_get(client):
    await client.post("/api/profile", json=PROFILE_PAYLOAD)
    await client.delete("/api/profile/testuser")
    response = await client.get("/api/profile/testuser")
    assert response.status_code == 404
