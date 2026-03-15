"""Tests for API routes."""


async def test_root_redirects_to_docs(client):
    """Test that root endpoint redirects to /docs."""
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


async def test_openapi_docs_accessible(client):
    """Test that OpenAPI docs are accessible."""
    response = await client.get("/docs")
    assert response.status_code == 200
