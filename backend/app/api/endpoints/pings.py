from fastapi import APIRouter

from app.core.services import EndpointBase, ServiceContainer
from app.utils.logging import LoggingService


class Pings(EndpointBase):
    """Example endpoint implemented as a class with static routes."""

    router = APIRouter(prefix="/ping", tags=["pings"])
    _logger: LoggingService

    def __init__(self, container: ServiceContainer):
        super().__init__(container)
        Pings._logger = container.logging

    @staticmethod
    @router.api_route("", methods=["GET", "HEAD", "OPTIONS"])
    async def ping_server():
        """Simple ping endpoint."""
        Pings._logger.info("ping_server called")
        return {"status": "ok"}


# Factory function to create router

def get_router(container: ServiceContainer) -> APIRouter:
    return Pings(container).router
