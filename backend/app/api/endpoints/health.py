from fastapi import APIRouter


class Health:
    """Health endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(tags=["health"])

    def __init__(self):
        """Initialize health endpoint."""
        pass

    @staticmethod
    @ep.get("/health")
    async def health_check():
        """Health check endpoint for the API."""
        return {"status": "ok"}


# Backward compatibility - create router instance
# This will be replaced when main.py is updated to use DIContainer
router = APIRouter()


@router.get("/health")
async def health_check_legacy():
    """
    Health check endpoint for the API.
    Returns:
        dict: A simple status message.
    """
    return {"status": "ok"}
