"""Tests for API routes."""


def test_root_redirects_to_docs(client):
    """Test that root endpoint redirects to /docs."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_get_sample_data(client):
    """Test /api/data endpoint."""
    response = client.get("/api/data")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert data["total"] == 3
    assert len(data["data"]) == 3
    assert data["data"][0]["id"] == 1
    assert data["data"][0]["name"] == "Sample Item 1"
    assert data["data"][0]["value"] == 100


def test_get_item(client):
    """Test /api/items/{item_id} endpoint."""
    response = client.get("/api/items/5")
    assert response.status_code == 200
    data = response.json()
    assert "item" in data
    assert data["item"]["id"] == 5
    assert data["item"]["name"] == "Sample Item 5"
    assert data["item"]["value"] == 500


def test_openapi_docs_accessible(client):
    """Test that OpenAPI docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
