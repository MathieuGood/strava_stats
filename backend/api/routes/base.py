from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint — API health check."""
    return {
        "message": "Strava Stats API",
        "version": "0.1.0",
        "status": "online",
    }


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
