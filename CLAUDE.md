# CLAUDE.md — Strava Stats

## Project Purpose

Personal tool that fetches cycling and sports activities from the Strava API, detects commute trips between two cities, calculates statistics, and generates Excel reimbursement reports.

The primary use case is tracking bike commutes between **Geispolsheim** and **Strasbourg** (France) for an employer reimbursement of **€0.25/km**.

---

## Project Structure

```
strava_stats/
├── docker-compose.yml       # Multi-container setup (backend + frontend)
├── Dockerfile.backend
├── Dockerfile.frontend
│
├── backend/                 # FastAPI REST API + CLI
│   ├── main.py              # CLI entry point (--fetch, --report)
│   ├── activities.json      # Cached Strava activities (source of truth)
│   ├── pyproject.toml
│   ├── .env                 # Strava OAuth credentials (never commit)
│   ├── api/
│   │   ├── app.py           # FastAPI app (CORS, lifespan, router registration)
│   │   ├── loader.py        # Global in-memory activity cache
│   │   └── routes/
│   │       ├── base.py      # Health check endpoints
│   │       └── activities.py # Activity endpoints (monthly totals, fetch, report)
│   └── strava/              # Strava logic package (single source of truth)
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
        │   ├── Home.vue     # Pivot table: years × months km grid with sport filter
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

Both servers must run simultaneously in separate terminals for the web UI to work.

```bash
# Terminal 1 — backend (must be running before opening the frontend)
cd backend && uvicorn api.app:app --reload

# Terminal 2 — frontend
cd frontend && npm run dev

# Docker (full stack — runs both automatically)
docker-compose up

# CLI: fetch all activities from Strava API
cd backend && uv run main.py --fetch

# CLI: rebuild activities.json from a Strava GDPR data export (see note below)
cd backend && uv run import_export.py /path/to/strava_export_XXXXXXXX

# CLI: generate monthly Excel report
cd backend && uv run main.py --report YYYY-MM

# Re-authorize Strava from scratch (if tokens are fully invalid)
cd backend && uv run reauth.py
```

---

## Strava API Access — Standard Tier subscription requirement (since 2026-06-30)

Strava now requires the API app owner to have an **active Strava subscription** to use Standard Tier API access (`/athlete/activities` etc.). Without it, every request returns:

```json
{"message":"Forbidden","errors":[{"resource":"Application","field":"Status","code":"Inactive"}]}
```

This is not a token/auth bug — `force_refresh()` won't fix it. As long as we don't pay for a subscription, `main.py --fetch` / `POST /activities/fetch` will keep failing with 403.

**Fallback: `import_export.py`.** Rebuilds `activities.json` from a Strava GDPR bulk data export ("Download your data" in Strava account settings — data becomes available for download after some delay). It parses `activities.csv` (French-locale headers/dates) plus the per-activity `.gpx`/`.gpx.gz`/`.tcx.gz`/`.fit.gz` files in `activities/` to reconstruct `start_latlng`/`end_latlng` (not present in the CSV, required for commute detection). Output matches the same schema `main.py --fetch` produces, so `storage.py`/`filter.py`/`stats.py`/`commute.py`/`report.py` and the API routes all work unchanged.

To refresh prod: run the script locally, then `scp backend/activities.json` to the VPS (`~/apps/strava_stats/backend/activities.json`) and restart the backend container (`docker compose -f docker-compose.prod.yml restart backend`) — there is no reload endpoint, the cache only loads at startup.

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

**Backend:** Python 3.12+, `fastapi`, `uvicorn`, `requests`, `openpyxl`, `python-dotenv`, `tzdata`, `anyio`, `fitdecode` (used by `import_export.py` to parse `.fit.gz` export files)

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

> **Note:** Strava uses **rotating refresh tokens** — each refresh invalidates the previous refresh token and issues a new one. If working across multiple machines, always keep the `.env` in sync with the machine that last performed a successful fetch. `StravaAuth` uses `load_dotenv(override=True)` and updates `os.environ` after every persist to ensure token state stays consistent within a running process.
>
> `StravaClient` automatically retries once on 401 by calling `auth.force_refresh()`, recovering from stale tokens without manual intervention. If tokens are fully invalidated (app deauthorized on Strava's side), run `uv run reauth.py` to go through the OAuth flow and write fresh tokens to `.env`.

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

## Commute Detection Logic (`backend/strava/commute.py`)

An activity is a commute if **all** of the following are true:

1. `start_latlng` and `end_latlng` are present
2. Start is within 5 km of City A and end is within 5 km of City B, **or** vice versa
3. Activity starts on a **weekday** (Mon–Fri)
4. Local start hour (Europe/Paris) is between 7 and 19

The `CommuteDetector` class is configurable — cities, radius, and hours can be overridden via constructor args (defaults come from `config.py`).

---

## Excel Report (`backend/strava/report.py`)

Output filename: `Indemnité_KM_mobilite_velo_MB_YYYY_MM.xlsx`

Columns:
| A: Date | B: Jour | C: Trajet Aller | D: Trajet Retour | E: Motif | F: Distance (km) | G: Indemnité/km | H: Indemnité (€) |

- Column B uses `=TEXT(A2,"jjjj")` for French day names
- Column H uses `=F*G` per row
- Final row sums columns F and H with `=SUM()`
- Multiple trips on the same day are grouped; distance is summed
- `generate()` saves to disk; `generate_to_bytes()` returns bytes for HTTP streaming

---

## Sport Aliases (`backend/strava/sports.py`)

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
- `StravaAuth` calls `load_dotenv(override=True)` so re-instantiation always picks up the latest token from disk; `_persist()` also writes new tokens directly to `os.environ` to keep in-process state consistent
