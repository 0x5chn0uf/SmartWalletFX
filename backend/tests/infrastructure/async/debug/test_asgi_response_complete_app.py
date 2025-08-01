import httpx
import pytest


@pytest.fixture(autouse=True)
def no_patch_httpx_async_client():
    """Disable global patching to use real httpx.AsyncClient."""
    pass


@pytest.mark.asyncio
async def test_fastapi_app_request_direct(test_app_with_di_container):
    """Make a basic request to FastAPI app using real httpx.AsyncClient."""
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200
