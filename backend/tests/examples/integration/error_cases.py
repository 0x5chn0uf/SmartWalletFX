import pytest

from tests.fixtures import client


def test_not_found_route(client):
    # Access a non-existent route
    resp = client.get("/nonexistent/path")
    assert resp.status_code == 404
