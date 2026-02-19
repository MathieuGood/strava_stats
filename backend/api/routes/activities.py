"""Routes for activity endpoints."""

from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter

from api.loader import get_activities

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
