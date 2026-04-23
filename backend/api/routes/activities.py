"""Routes for activity endpoints."""

from collections import defaultdict
from datetime import date, datetime, timedelta
from io import BytesIO
from urllib.parse import quote

from anyio import to_thread
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from api.loader import DATA_PATH, get_activities, load_activities
from strava import ActivityStorage, CommuteDetector, CommuteReport, StravaAuth, StravaClient

router = APIRouter(prefix="/activities", tags=["activities"])

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


@router.get("/all-detail")
async def get_all_activities_detail():
    """Return all activities with detail fields, sorted chronologically."""
    activities = get_activities()
    result = []
    for a in activities:
        start_dt = datetime.fromisoformat(a["start_date_local"].replace("Z", "+00:00"))
        elapsed = a.get("elapsed_time", 0)
        end_dt = start_dt + timedelta(seconds=elapsed)
        result.append({
            "id": a.get("id"),
            "datetime": start_dt.strftime("%Y-%m-%d %H:%M"),
            "end_time": end_dt.strftime("%H:%M"),
            "name": a.get("name"),
            "sport_type": a.get("sport_type"),
            "distance_km": round(a.get("distance", 0) / 1000, 2),
            "moving_time_s": a.get("moving_time", 0),
            "elevation_m": a.get("total_elevation_gain", 0),
            "avg_speed_kmh": round(a.get("average_speed", 0) * 3.6, 1),
            "avg_heartrate": a.get("average_heartrate"),
            "commute": a.get("commute", False),
        })
    result.sort(key=lambda x: x["datetime"])
    return result


@router.get("/by-month")
async def get_activities_by_month(year: int, month: int):
    """Return detailed activities for a given year/month, sorted chronologically."""
    activities = get_activities()
    result = []
    for a in activities:
        dt = datetime.fromisoformat(a["start_date_local"].replace("Z", "+00:00"))
        if dt.year != year or dt.month != month:
            continue
        start_dt = datetime.fromisoformat(a["start_date_local"].replace("Z", "+00:00"))
        elapsed = a.get("elapsed_time", 0)
        end_dt = start_dt + timedelta(seconds=elapsed)
        result.append({
            "id": a.get("id"),
            "date": a["start_date_local"][:10],
            "start_time": start_dt.strftime("%H:%M"),
            "end_time": end_dt.strftime("%H:%M"),
            "name": a.get("name"),
            "sport_type": a.get("sport_type"),
            "distance_km": round(a.get("distance", 0) / 1000, 2),
            "moving_time_s": a.get("moving_time", 0),
            "elevation_m": a.get("total_elevation_gain", 0),
            "avg_speed_kmh": round(a.get("average_speed", 0) * 3.6, 1),
            "avg_heartrate": a.get("average_heartrate"),
            "commute": a.get("commute", False),
        })
    result.sort(key=lambda x: x["date"])
    return result


@router.get("/export")
async def export_activities():
    """Download the raw activities.json file."""
    return FileResponse(DATA_PATH, media_type="application/json", filename="activities.json")


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


def _period_of_date(d: date) -> tuple[int, int]:
    """Return the (year, month) reporting period a date belongs to.

    Periods run from the 21st of the previous month to the 20th of the returned month.
    E.g. Dec 22 → (year+1 if Dec, 1) = January of next year.
         Jan 5  → (year, 1) = January.
         Jan 21 → (year, 2) = February.
    """
    if d.day >= 21:
        if d.month == 12:
            return d.year + 1, 1
        return d.year, d.month + 1
    return d.year, d.month


@router.get("/commute-months")
async def get_commute_months():
    """Return the list of reporting periods that contain commute activities."""
    activities = get_activities()
    detector = CommuteDetector()
    commutes = detector.get_commute_activities(activities)

    periods: set[tuple[int, int]] = set()
    for c in commutes:
        periods.add(_period_of_date(c["date"]))

    return [
        {"year": y, "month": m, "label": f"{MONTH_NAMES[m - 1]} {y}"}
        for y, m in sorted(periods, reverse=True)
    ]


@router.get("/report")
async def download_report(year: int, month: int):
    """Generate and stream an Excel commute report for the given period (21st prev → 20th)."""
    activities = get_activities()
    detector = CommuteDetector()
    commutes = detector.get_commute_activities(activities)

    prev_month = 12 if month == 1 else month - 1
    prev_year = year - 1 if month == 1 else year
    start_date = date(prev_year, prev_month, 21)
    end_date = date(year, month, 20)

    filtered = [c for c in commutes if start_date <= c["date"] <= end_date]

    def _generate() -> bytes:
        return CommuteReport(filtered, year, month).generate_to_bytes()

    try:
        xlsx_bytes = await to_thread.run_sync(_generate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    filename = f"Indemnité_KM_mobilite_velo_MB_{year}_{month:02d}.xlsx"
    encoded_filename = quote(filename)

    return StreamingResponse(
        BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )
