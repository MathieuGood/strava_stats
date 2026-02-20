"""Routes for activity endpoints."""

from collections import defaultdict
from datetime import datetime

from anyio import to_thread
from fastapi import APIRouter, HTTPException

from api.loader import DATA_PATH, get_activities, load_activities
from strava import ActivityStorage, StravaAuth, StravaClient

router = APIRouter(prefix="/activities", tags=["activities"])

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


@router.get("/monthly-totals")
async def get_monthly_totals():
    """Return total distance in km per (year, month, sport_type)."""
    activities = get_activities()

    totals: dict[tuple[int, int, str], float] = defaultdict(float)
    for a in activities:
        dt = datetime.fromisoformat(a["start_date"].replace("Z", "+00:00"))
        sport = a.get("sport_type", "Unknown")
        totals[(dt.year, dt.month, sport)] += a.get("distance", 0)

    result = [
        {
            "year": year,
            "month": month,
            "month_name": MONTH_NAMES[month - 1],
            "sport_type": sport,
            "total_km": round(dist_m / 1000, 1),
        }
        for (year, month, sport), dist_m in totals.items()
    ]

    result.sort(key=lambda r: (r["year"], r["month"]), reverse=True)
    return result


@router.post("/fetch")
async def fetch_from_strava():
    """Fetch all activities from the Strava API, persist to disk, and reload the cache."""
    def _do_fetch() -> int:
        auth = StravaAuth()
        client = StravaClient(auth)
        activities = client.fetch_all_activities()
        ActivityStorage(DATA_PATH).save(activities)
        load_activities()
        return len(activities)

    try:
        count = await to_thread.run_sync(_do_fetch)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"fetched": count}
