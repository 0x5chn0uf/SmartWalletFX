"""
Test module for health check endpoint

Coverage:
- Basic health check response
- Response format validation

Dependencies:
- FastAPI TestClient
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """
    Given: A running FastAPI application
    When: GET request is made to /api/v1/health
    Then: Returns 200 status and healthy message
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
 