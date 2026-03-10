# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtual environment (always required first)
source venv/bin/activate

# Run the development server
uvicorn app.main:app --reload

# Import F1 data into the database (drops and recreates all F1 tables, preserves users)
python -m data.import_csv

# Run tests (no test files exist yet)
pytest
```

API is available at `http://localhost:8000`, docs at `/docs` and `/redoc`.

## Environment

Config is loaded from `.env` via `app/config.py` (pydantic-settings). Key variables:
- `DATABASE_URL` — defaults to `postgresql://surewu@localhost:5432/f1_insight`
- `SECRET_KEY` — JWT signing key
- `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT expiry (default 30)

## Architecture

**Request flow:** FastAPI router → direct SQLAlchemy query (no service layer in practice) → return dict

There is no active service layer (`app/services/` is empty). All business logic lives directly in the router functions.

**Database session** is injected per-request via `Depends(get_db)` (defined in `app/database.py`).

**Auth** (`app/utils/auth.py`) provides two FastAPI dependencies:
- `get_current_user` — requires valid JWT, returns User
- `require_admin` — requires `user.role == "admin"`

## Data Model

10 tables imported from Ergast F1 CSV dataset (1950–2024). Import order matters due to foreign keys:

`seasons` → `circuits` → `drivers` → `constructors` → `status` → `races` → `results` → `qualifying` → `pit_stops` → `lap_times`

4 CSV files intentionally not imported (`driver_standings`, `constructor_standings`, `constructor_results`, `sprint_results`) — their data is derived at query time via aggregation in the analytics endpoints.

**PitStop** and **LapTime** use surrogate autoincrement PKs with a composite index on `(race_id, driver_id)`. Natural key would be `(race_id, driver_id, stop/lap)` but ORM ergonomics favour the surrogate key.

## Router Overview

| File | Prefix | Notes |
|------|--------|-------|
| `routers/auth.py` | `/api/v1/auth` | Register, login (returns JWT) |
| `routers/drivers.py` | `/api/v1/drivers` | Full CRUD; DELETE requires admin |
| `routers/circuits.py` | `/api/v1/circuits` | Full CRUD; POST/PUT require auth, DELETE requires admin |
| `routers/constructors.py` | `/api/v1/constructors` | Full CRUD; POST/PUT require auth, DELETE requires admin |
| `routers/analytics.py` | `/api/v1/analytics` | Career stats, season progression, driver compare, pit stop analysis, circuit history |
| `routers/advanced_analytics.py` | `/api/v1/analytics` | Win probability, performance summary, teammate battle, leaderboard |

Both analytics routers share the same URL prefix — route ordering matters to avoid conflicts (e.g. `/drivers/compare` must be registered before `/drivers/{driver_id}`).

## List Endpoint Pattern (circuits, constructors)

`GET /` returns a `*ListResponse` schema that includes aggregated stats (e.g. `total_races`, `total_points`, `wins`) so sort order is meaningful to the caller.

**Implementation:** a single stats subquery (`GROUP BY` on the join table) is computed once and `outerjoin`-ed into the main query. All sort modes (`most_races`, `total_points`, `wins`, `recent`) reference columns from this subquery — no repeated joins per sort branch.

**`sort_by=recent` pattern:** use `last_year` (MAX race year) from the subquery, not a `WHERE year == latest_season` filter. The filter approach silently drops historical records that don't match; the subquery approach keeps all rows and ranks them by recency (missing = 0).

**`sort_by=recent` in drivers.py** uses a different approach: a dedicated subquery filtered to `latest_season` computes points for that season only, then `outerjoin`-ed so historical drivers appear with 0 points instead of disappearing.

## Known Design Decisions

- **Analytics compute from raw data** — no pre-aggregated standings tables. `SUM`/`GROUP BY` over `results` is intentional to demonstrate query capability.
- **Pit stop outlier filtering** — stops `>= 45000ms` are excluded from efficiency calculations to remove red flag anomalies. Use median, not mean.
- **Overtaking score** — per-race scoring with front-row compensation: if a driver starts and finishes in the top 3, they receive 100 for that race (avoids penalising drivers who have no cars ahead to pass).
- **N+1 queries fixed** in `analytics.py`: `compare_drivers` and `get_pit_stop_analysis` both use `.in_()` bulk fetches + dict lookups instead of per-row queries.
- **`Result.position`** is `Integer` (nullable) — safe to compare with `== 1` directly. Use `case((Result.position == 1, 1), else_=0)` for conditional counting, not `func.cast(bool_expr, Integer)`.
