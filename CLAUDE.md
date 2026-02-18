# CLAUDE.md — Strava Stats

## Project Purpose

Personal Python tool that fetches cycling and sports activities from the Strava API, detects commute trips between two cities, calculates statistics, and generates Excel reimbursement reports.

The primary use case is tracking bike commutes between **Geispolsheim** and **Strasbourg** (France) for an employer reimbursement of **€0.25/km**.

---

## Project Structure

```
strava_stats/
├── main.py                  # CLI entry point
├── activities.json          # Local cache of Strava activities (gitignored if sensitive)
├── reports/                 # Generated Excel reports (output directory)
├── pyproject.toml           # Project metadata and dependencies
├── .env                     # Strava OAuth credentials (never commit)
└── strava/                  # Main package
    ├── __init__.py          # Public exports
    ├── auth.py              # OAuth token management + auto-refresh
    ├── client.py            # Strava REST API client (paginated fetch)
    ├── commute.py           # Commute detection (haversine + work hours)
    ├── config.py            # City coordinates, thresholds, rate
    ├── filter.py            # Fluent activity filtering (sport, year, date range)
    ├── report.py            # Excel (.xlsx) report generation via openpyxl
    ├── sports.py            # Sport alias normalization (e.g. "biking" → "Ride")
    ├── stats.py             # Statistics (km by sport, year, chainable filters)
    └── storage.py           # JSON persistence for cached activities
```

---

## Commands

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Fetch all activities from Strava API → saves to activities.json
python main.py --fetch

# Generate monthly Excel report
python main.py --report YYYY-MM

# Print statistics to stdout (default, no args)
python main.py
```

---

## Dependencies

- Python 3.12+
- `requests` — HTTP client for Strava API calls
- `openpyxl` — Excel report generation
- `python-dotenv` — Load `.env` credentials
- `tzdata` — Timezone data (used with `zoneinfo` for Europe/Paris)

Install: `pip install -e .` or `pip install -r` from `pyproject.toml`.

---

## Environment Variables (`.env`)

Required in project root. Auto-updated on token refresh.

```
CLIENT_ID=<strava_client_id>
CLIENT_SECRET=<strava_client_secret>
ACCESS_TOKEN=<strava_access_token>
REFRESH_TOKEN=<strava_refresh_token>
EXPIRES_AT=<unix_timestamp>
```

---

## Key Configuration (`strava/config.py`)

| Setting            | Value              | Description                                      |
|--------------------|--------------------|--------------------------------------------------|
| `CITY_A`           | Geispolsheim       | lat: 48.5147, lon: 7.6467                       |
| `CITY_B`           | Strasbourg         | lat: 48.5734, lon: 7.7521                       |
| `RADIUS_KM`        | 5                  | Max distance from city center to count as "in city" |
| `WORK_HOUR_START`  | 7                  | Start of valid commute window (Europe/Paris)     |
| `WORK_HOUR_END`    | 19                 | End of valid commute window (Europe/Paris)       |
| `TIMEZONE`         | Europe/Paris       | Used for weekday and hour filtering              |
| `RATE_PER_KM`      | 0.25               | Reimbursement rate in euros                      |

---

## Architecture & Data Flow

```
Strava API
    │
    ▼
StravaAuth       — loads .env, auto-refreshes OAuth token
    │
    ▼
StravaClient     — paginates GET /athlete/activities (200/page)
    │
    ▼
ActivityStorage  — persists to / loads from activities.json
    │
    ├──▶ ActivityFilter   — fluent filter by sport/year/date range
    │        │
    │        └──▶ ActivityStats   — km totals (by sport, year, chainable)
    │
    └──▶ CommuteDetector  — haversine distance + weekday/hour check
             │
             └──▶ CommuteReport  — openpyxl Excel with formulas + totals
```

---

## Commute Detection Logic (`strava/commute.py`)

An activity is a commute if **all** of the following are true:

1. `start_latlng` and `end_latlng` are present
2. Start is within 5 km of City A and end is within 5 km of City B, **or** vice versa
3. Activity starts on a **weekday** (Mon–Fri)
4. Local start hour (Europe/Paris) is between 7 and 19

The `CommuteDetector` class is configurable — cities, radius, and hours can be overridden via constructor args (defaults come from `config.py`).

---

## Excel Report (`strava/report.py`)

Output: `reports/Indemnité_KM_mobilite_velo_MB_YYYY_MM.xlsx`

Columns:
| A: Date | B: Jour | C: Trajet Aller | D: Trajet Retour | E: Motif | F: Distance (km) | G: Indemnité/km | H: Indemnité (€) |

- Column B uses `=TEXT(A2,"jjjj")` for French day names
- Column H uses `=F*G` per row
- Final row sums columns F and H with `=SUM()`
- Multiple trips on the same day are grouped; distance is summed

---

## Sport Aliases (`strava/sports.py`)

User-facing aliases map to Strava `sport_type` values:

| Alias(es)                        | Strava Type      |
|----------------------------------|------------------|
| bike, biking, ride               | Ride             |
| inline, inline_skate, inline skating | InlineSkate  |
| roller, rollerski                | RollerSki        |
| run, running                     | Run              |
| walk, walking                    | Walk             |
| sup, stand up paddling           | StandUpPaddling  |

---

## Coding Conventions

- No test suite currently — logic is exercised via `main.py` runs
- `ActivityStats` and `ActivityFilter` are chainable: `stats.by_sport("biking").by_year(2025).total_km()`
- All distance stored in **meters** (from Strava), converted to **km** at display/report time
- Dates parsed from ISO 8601 UTC strings; timezone conversion uses `zoneinfo.ZoneInfo`
- `activities.json` is the single source of truth for local data; always `--fetch` before stats if freshness matters
