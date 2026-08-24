"""One-shot importer: rebuild activities.json from a Strava GDPR bulk export.

Strava's Standard Tier API now requires the app owner to have an active
Strava subscription (policy change effective 2026-06-30). Until/unless we
pay for that, this script is the replacement for `main.py --fetch`: it
reads the CSV + per-activity GPX/TCX/FIT files from a Strava data export
("Download your data" from account settings) and reconstructs
activities.json in the same schema the rest of the app expects.

Usage:
    uv run import_export.py /path/to/strava_export_XXXXXXXX
"""

import csv
import gzip
import io
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

import fitdecode

from strava import ActivityStorage, CommuteDetector

TZ = ZoneInfo("Europe/Paris")

FR_MONTHS = {
    "janv.": 1, "janvier": 1,
    "févr.": 2, "février": 2,
    "mars": 3,
    "avr.": 4, "avril": 4,
    "mai": 5,
    "juin": 6,
    "juil.": 7, "juillet": 7,
    "août": 8,
    "sept.": 9, "septembre": 9,
    "oct.": 10, "octobre": 10,
    "nov.": 11, "novembre": 11,
    "déc.": 12, "décembre": 12,
}

SPORT_TYPE_MAP = {
    "Vélo": "Ride",
    "Roller": "InlineSkate",
    "Course à pied": "Run",
    "Marche": "Walk",
    "Stand up paddle": "StandUpPaddling",
    "Ski à roulettes": "RollerSki",
}

GPX_NS = "{http://www.topografix.com/GPX/1/1}"
TCX_NS = "{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}"


def parse_fr_date(raw: str) -> datetime:
    """'18 août 2026, 15:30:25' -> naive local datetime (Europe/Paris wall clock)."""
    date_part, time_part = raw.split(", ")
    day_str, month_fr, year_str = date_part.split(" ")
    month = FR_MONTHS[month_fr.lower()]
    h, m, s = (int(x) for x in time_part.split(":"))
    return datetime(int(year_str), month, int(day_str), h, m, s)


def _open_maybe_gz(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rb")
    return open(path, "rb")


def extract_latlng_gpx(path: Path):
    with _open_maybe_gz(path) as f:
        content = f.read().lstrip()
    root = ET.fromstring(content)
    pts = root.findall(f".//{GPX_NS}trkpt") or root.findall(".//trkpt")
    if not pts:
        return None, None
    first, last = pts[0], pts[-1]
    return [float(first.get("lat")), float(first.get("lon"))], [
        float(last.get("lat")),
        float(last.get("lon")),
    ]


def _find_any(el, ns_tag: str, plain_tag: str):
    found = el.find(ns_tag)
    return found if found is not None else el.find(plain_tag)


def extract_latlng_tcx(path: Path):
    with _open_maybe_gz(path) as f:
        content = f.read().lstrip()
    root = ET.fromstring(content)
    trkpts = root.findall(f".//{TCX_NS}Trackpoint")
    if not trkpts:
        trkpts = root.findall(".//Trackpoint")
    coords = []
    for tp in trkpts:
        pos = _find_any(tp, f"{TCX_NS}Position", "Position")
        if pos is None:
            continue
        lat_el = _find_any(pos, f"{TCX_NS}LatitudeDegrees", "LatitudeDegrees")
        lon_el = _find_any(pos, f"{TCX_NS}LongitudeDegrees", "LongitudeDegrees")
        if lat_el is None or lon_el is None:
            continue
        coords.append([float(lat_el.text), float(lon_el.text)])
    if not coords:
        return None, None
    return coords[0], coords[-1]


def extract_latlng_fit(path: Path):
    with gzip.open(path, "rb") as f:
        buf = io.BytesIO(f.read())
    coords = []
    with fitdecode.FitReader(buf) as fit:
        for frame in fit:
            if frame.frame_type != fitdecode.FIT_FRAME_DATA or frame.name != "record":
                continue
            lat = frame.get_value("position_lat", fallback=None)
            lon = frame.get_value("position_long", fallback=None)
            if lat is None or lon is None:
                continue
            coords.append([lat * (180 / 2**31), lon * (180 / 2**31)])
    if not coords:
        return None, None
    return coords[0], coords[-1]


def extract_latlng(export_dir: Path, filename: str):
    if not filename:
        return None, None
    path = export_dir / filename
    if not path.exists():
        return None, None
    try:
        if filename.endswith((".fit.gz", ".fit")):
            return extract_latlng_fit(path)
        if filename.endswith((".tcx.gz", ".tcx")):
            return extract_latlng_tcx(path)
        if filename.endswith((".gpx.gz", ".gpx")):
            return extract_latlng_gpx(path)
    except Exception as e:
        print(f"  WARN: failed to parse {filename}: {e}")
    return None, None


def build_activity(row: list[str], export_dir: Path) -> dict | None:
    activity_id = row[0]
    if not activity_id:
        return None

    sport_fr = row[3]
    sport_type = SPORT_TYPE_MAP.get(sport_fr, sport_fr)

    local_dt = parse_fr_date(row[1]).replace(tzinfo=TZ)
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

    distance_m = float(row[17]) if row[17] else 0.0
    elapsed_time = int(float(row[15])) if row[15] else 0
    moving_time = int(float(row[16])) if row[16] else elapsed_time
    elevation_gain = float(row[20]) if row[20] else 0.0
    avg_speed = float(row[19]) if row[19] else 0.0
    avg_heartrate = float(row[31]) if row[31] else None

    start_latlng, end_latlng = extract_latlng(export_dir, row[12])

    return {
        "id": int(activity_id),
        "name": row[2],
        "distance": distance_m,
        "moving_time": moving_time,
        "elapsed_time": elapsed_time,
        "total_elevation_gain": elevation_gain,
        "type": sport_type,
        "sport_type": sport_type,
        "start_date": utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "start_date_local": local_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "start_latlng": start_latlng,
        "end_latlng": end_latlng,
        "average_speed": avg_speed,
        "average_heartrate": avg_heartrate,
        "commute": False,
    }


def print_completeness(activities: list[dict], months: int = 4):
    """Summarise the tail of the export so it can be checked against Strava.

    A GDPR export is only as fresh as the moment Strava built it, and the
    last weeks are the ones that go missing. Print the recent months so the
    counts can be compared with what the Strava app actually shows before
    any report is generated from this data.
    """
    if not activities:
        print("No activities in the export.")
        return

    per_month = defaultdict(int)
    for a in activities:
        per_month[a["start_date_local"][:7]] += 1

    recent = sorted(per_month)[-months:]
    last_date = activities[-1]["start_date_local"][:10]

    print("\nActivities per month (tail of the export):")
    for ym in recent:
        print(f"  {ym}: {per_month[ym]}")
    print(f"Most recent activity: {last_date}")
    print(
        "\n  CHECK: compare these counts with the Strava app before generating\n"
        "  reports. An export built before your last rides will silently be\n"
        "  missing them, and a report for that period will under-report km."
    )


def main():
    if len(sys.argv) != 2:
        print("Usage: uv run import_export.py /path/to/strava_export_XXXXXXXX")
        sys.exit(1)

    export_dir = Path(sys.argv[1]).expanduser().resolve()
    csv_path = export_dir / "activities.csv"
    if not csv_path.exists():
        print(f"activities.csv not found in {export_dir}")
        sys.exit(1)

    activities = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # header
        for i, row in enumerate(reader):
            activity = build_activity(row, export_dir)
            if activity is None:
                continue
            activities.append(activity)
            if (i + 1) % 200 == 0:
                print(f"  processed {i + 1} rows...")

    detector = CommuteDetector()
    for a in activities:
        a["commute"] = detector.is_commute(a)

    activities.sort(key=lambda a: a["start_date"])

    data_path = Path(__file__).parent / "activities.json"
    ActivityStorage(str(data_path)).save(activities)

    n_commutes = sum(1 for a in activities if a["commute"])
    n_with_latlng = sum(1 for a in activities if a["start_latlng"])
    print(f"Done: {len(activities)} activities, {n_with_latlng} with GPS, {n_commutes} detected commutes.")

    print_completeness(activities)


if __name__ == "__main__":
    main()
