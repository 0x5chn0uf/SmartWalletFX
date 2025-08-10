import httpx
import pytest
from fastapi import FastAPI


@pytest.fixture(autouse=True)
def no_patch_httpx_async_client():
    """Override global patch fixture to use real httpx.AsyncClient."""
    # Intentionally do nothing so httpx.AsyncClient is unpatched
    pass


def create_test_app():
    app = FastAPI()

    @app.get("/ping")
    async def ping():
        return {"message": "pong"}

    return app


@pytest.mark.asyncio
async def test_async_client_with_asgi_transport_fails():
    """Demonstrate failure when using httpx.AsyncClient with ASGI transport."""
    app = create_test_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ping")
        assert resp.status_code == 200
        assert resp.json() == {"message": "pong"}
