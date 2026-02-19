from contextlib import asynccontextmanager

from anyio import to_thread
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.loader import load_activities
from api.routes import base, activities


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context: pre-load activities at startup."""
    try:
        ok = await to_thread.run_sync(load_activities)
        print(f"Startup: activities loaded -> {ok}")
    except Exception as e:
        print(f"Startup: failed to load activities: {e}")
    yield


app = FastAPI(
    title="Strava Stats API",
    description="API for Strava activity statistics",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(base.router)
app.include_router(activities.router)
