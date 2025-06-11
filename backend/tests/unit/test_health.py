"""
Test module for health check endpoint

Coverage:
- Basic health check response
- Response format validation

Dependencies:
- FastAPI TestClient
"""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """
    Given: A running FastAPI application
    When: GET request is made to /health
    Then: Returns 200 status and healthy message
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
