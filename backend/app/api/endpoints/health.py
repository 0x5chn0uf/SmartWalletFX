from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the API.
    Returns:
        dict: A simple status message.
    """
    return {"status": "ok"}
