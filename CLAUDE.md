# CLAUDE.md — Strava Stats

## Project Purpose

Personal tool that fetches cycling and sports activities from the Strava API, detects commute trips between two cities, calculates statistics, and generates Excel reimbursement reports.

The primary use case is tracking bike commutes between **Geispolsheim** and **Strasbourg** (France) for an employer reimbursement of **€0.25/km**.

---

## Project Structure

```
strava_stats/
├── main.py                  # CLI entry point (legacy)
├── pyproject.toml           # Root CLI dependencies
├── docker-compose.yml       # Multi-container setup (backend + frontend)
├── Dockerfile.backend
├── Dockerfile.frontend
│
├── backend/                 # FastAPI REST API
│   ├── activities.json      # Cached Strava activities (source of truth)
│   ├── pyproject.toml
│   ├── .env                 # Strava OAuth credentials (never commit)
│   ├── api/
│   │   ├── app.py           # FastAPI app (CORS, lifespan, router registration)
│   │   ├── loader.py        # Global in-memory activity cache
│   │   └── routes/
│   │       ├── base.py      # Health check endpoints
│   │       └── activities.py # Activity endpoints (monthly totals, fetch, report)
│   └── strava/              # Strava logic package (mirrored from root /strava)
│       ├── __init__.py      # Public exports
│       ├── auth.py          # OAuth token management + auto-refresh
│       ├── client.py        # Strava REST API client (paginated fetch)
│       ├── commute.py       # Commute detection (haversine + work hours)
│       ├── config.py        # City coordinates, thresholds, rate
│       ├── filter.py        # Fluent activity filtering (sport, year, date range)
│       ├── report.py        # Excel (.xlsx) report generation via openpyxl
│       ├── sports.py        # Sport alias normalization (e.g. "biking" → "Ride")
│       ├── stats.py         # Statistics (km by sport, year, chainable filters)
│       └── storage.py       # JSON persistence for cached activities
│
└── frontend/                # Vue 3 + TypeScript SPA (Vite)
    └── src/
        ├── main.ts          # App entry (PrimeVue MidnightAmber theme)
        ├── App.vue          # Root component
        ├── components/
        │   └── Header.vue   # Nav bar + "Fetch new data" button
        ├── pages/
        │   ├── Home.vue     # Monthly totals table with sport filter
        │   ├── Charts.vue   # ECharts line/bar charts with sport + year filters
        │   └── Reports.vue  # Report download page with month dropdown
        ├── fetch/
        │   └── fetchActivities.ts  # API client functions
        └── router/
            └── index.ts     # Vue Router: /, /charts, /reports
```

---

## Backend API Endpoints

| Method | Path                          | Description                                              |
|--------|-------------------------------|----------------------------------------------------------|
| GET    | `/`                           | Health / API info                                        |
| GET    | `/health`                     | Health check                                             |
| GET    | `/activities/monthly-totals`  | km per (year, month, sport_type)                        |
| POST   | `/activities/fetch`           | Sync from Strava API, persist, reload cache             |
| GET    | `/activities/commute-months`  | Periods with commute data (for report dropdown)         |
| GET    | `/activities/report?year=&month=` | Stream Excel report for the given period           |

---

## Reporting Period Convention

Reports run from the **21st of the previous month** to the **20th of the selected month**.

- "January 2026" → Dec 21 2025 → Jan 20 2026
- An activity on Dec 22 belongs to the January period; Dec 15 belongs to December.

This applies to both the CLI (`--report YYYY-MM`) and the web `/activities/report` endpoint.

---

## Commands

```bash
# Run backend (dev)
cd backend && uvicorn api.app:app --reload

# Run frontend (dev)
cd frontend && npm run dev

# Docker (full stack)
docker-compose up

# CLI: fetch all activities from Strava API
python main.py --fetch

# CLI: generate monthly Excel report
python main.py --report YYYY-MM
```

---

## Frontend Stack

- **Vue 3** with Composition API (`<script setup>`)
- **TypeScript** (strict)
- **Tailwind CSS** v4
- **PrimeVue** v4.5 — DataTable, MultiSelect, Select
- **ECharts** v6 via vue-echarts — line chart (monthly km per year) + bar chart (yearly totals)
- **Vue Router** — `/`, `/charts`, `/reports`

---

## Dependencies

**Backend:** Python 3.12+, `fastapi`, `uvicorn`, `requests`, `openpyxl`, `python-dotenv`, `tzdata`, `anyio`

**Frontend:** Vue 3, Vite, TypeScript, Tailwind CSS, PrimeVue, ECharts, vue-echarts

---

## Environment Variables (`backend/.env`)

Required. Auto-updated on token refresh.

```
CLIENT_ID=<strava_client_id>
CLIENT_SECRET=<strava_client_secret>
ACCESS_TOKEN=<strava_access_token>
REFRESH_TOKEN=<strava_refresh_token>
EXPIRES_AT=<unix_timestamp>
```

---

## Key Configuration (`backend/strava/config.py`)

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
ActivityStorage  — persists to / loads from backend/activities.json
    │
    ├──▶ ActivityFilter   — fluent filter by sport/year/date range
    │        │
    │        └──▶ ActivityStats   — km totals (by sport, year, chainable)
    │
    └──▶ CommuteDetector  — haversine distance + weekday/hour check
             │
             └──▶ CommuteReport  — openpyxl Excel; generate() → file,
                                   generate_to_bytes() → bytes (HTTP stream)
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

Output filename: `Indemnité_KM_mobilite_velo_MB_YYYY_MM.xlsx`

Columns:
| A: Date | B: Jour | C: Trajet Aller | D: Trajet Retour | E: Motif | F: Distance (km) | G: Indemnité/km | H: Indemnité (€) |

- Column B uses `=TEXT(A2,"jjjj")` for French day names
- Column H uses `=F*G` per row
- Final row sums columns F and H with `=SUM()`
- Multiple trips on the same day are grouped; distance is summed
- `generate()` saves to disk; `generate_to_bytes()` returns bytes for HTTP streaming

---

## Sport Aliases (`strava/sports.py`)

| Alias(es)                            | Strava Type      |
|--------------------------------------|------------------|
| bike, biking, ride                   | Ride             |
| inline, inline_skate, inline skating | InlineSkate      |
| roller, rollerski                    | RollerSki        |
| run, running                         | Run              |
| walk, walking                        | Walk             |
| sup, stand up paddling               | StandUpPaddling  |

---

## Coding Conventions

- No test suite — logic is exercised via `main.py` runs and the web UI
- `ActivityStats` and `ActivityFilter` are chainable: `stats.by_sport("biking").by_year(2025).total_km()`
- All distances stored in **meters** (from Strava), converted to **km** at display/report time
- Dates parsed from ISO 8601 UTC strings; timezone conversion uses `zoneinfo.ZoneInfo`
- `backend/activities.json` is the single source of truth for local data
- Backend uses `anyio.to_thread.run_sync()` to run sync Strava/openpyxl code without blocking the event loop
