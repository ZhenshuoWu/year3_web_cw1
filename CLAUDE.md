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

# Run tests
pytest

# Run tests with coverage report
pytest --cov=app --cov-report=term-missing
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

## Database

### Tech Stack

- **DBMS**: PostgreSQL (local dev: `postgresql://surewu@localhost:5432/f1_insight`, production: Render PostgreSQL)
- **ORM**: SQLAlchemy 2.0 (declarative base via `DeclarativeBase`)
- **Session management**: `sessionmaker` with per-request `get_db()` dependency (`app/database.py`)
- **Config**: `DATABASE_URL` loaded from `.env` via pydantic-settings (`app/config.py`)
- **Render compatibility**: auto-replaces `postgres://` → `postgresql://` at startup (SQLAlchemy 2.0+ requirement)

### Database Construction

Database is built in two parts:

1. **Schema creation**: `Base.metadata.create_all(bind=engine)` in `data/import_csv.py` creates all tables from SQLAlchemy models (`app/models/models.py`). No Alembic migrations — schema is managed entirely through model definitions.

2. **Data import** (`python -m data.import_csv`):
   - Reads 10 CSV files from `data/` directory (Ergast F1 dataset, 1950–2024)
   - Drops and recreates F1 data tables only (preserves `users` table)
   - Imports in FK-respecting order within a single transaction (rollback on failure)
   - Uses pandas `to_sql()` with `chunksize=5000` for bulk insert
   - CSV column names are mapped from camelCase to snake_case via `COLUMN_MAPPINGS` dict
   - `\N` and empty strings in CSV are cleaned to `None`

4 CSV files intentionally not imported (`driver_standings`, `constructor_standings`, `constructor_results`, `sprint_results`) — their data is derived at query time via aggregation in the analytics endpoints.

### Table Structure (11 tables)

**F1 Data Tables** (10 tables, imported from CSV):

Import order: `seasons` → `circuits` → `drivers` → `constructors` → `status` → `races` → `results` → `qualifying` → `pit_stops` → `lap_times`

| Table | PK | Key Columns | Foreign Keys | Indexes |
|-------|-----|-------------|--------------|---------|
| `seasons` | `year` (INT) | `url` | — | — |
| `circuits` | `circuit_id` (INT) | `circuit_ref`, `name`, `location`, `country`, `lat`, `lng`, `alt`, `url` | — | — |
| `drivers` | `driver_id` (INT) | `driver_ref`, `number`?, `code`?, `forename`, `surname`, `dob`?, `nationality`, `url` | — | — |
| `constructors` | `constructor_id` (INT) | `constructor_ref`, `name`, `nationality`, `url` | — | — |
| `status` | `status_id` (INT) | `status` | — | — |
| `races` | `race_id` (INT) | `year`, `round`, `circuit_id`, `name`, `date`, `time`?, `url`, `fp1/fp2/fp3/quali/sprint_date`?, `fp1/fp2/fp3/quali/sprint_time`? | `year` → `seasons.year`, `circuit_id` → `circuits.circuit_id` | `ix_races_year`, `ix_races_circuit_id` |
| `results` | `result_id` (INT) | `race_id`, `driver_id`, `constructor_id`, `number`?, `grid`, `position`?, `position_text`, `position_order`, `points`, `laps`, `time`?, `milliseconds`?, `fastest_lap`?, `rank`?, `fastest_lap_time`?, `fastest_lap_speed`?, `status_id` | `race_id` → `races.race_id`, `driver_id` → `drivers.driver_id`, `constructor_id` → `constructors.constructor_id`, `status_id` → `status.status_id` | `ix_results_race_id`, `ix_results_driver_id`, `ix_results_constructor_id` |
| `qualifying` | `qualify_id` (INT) | `race_id`, `driver_id`, `constructor_id`, `number`?, `position`?, `q1`?, `q2`?, `q3`? | `race_id` → `races.race_id`, `driver_id` → `drivers.driver_id`, `constructor_id` → `constructors.constructor_id` | `ix_qualifying_race_id`, `ix_qualifying_driver_id` |
| `pit_stops` | `id` (INT, auto) | `race_id`, `driver_id`, `stop`, `lap`, `time`?, `duration`?, `milliseconds`? | `race_id` → `races.race_id`, `driver_id` → `drivers.driver_id` | composite `ix_pit_stops_race_driver` on `(race_id, driver_id)` |
| `lap_times` | `id` (INT, auto) | `race_id`, `driver_id`, `lap`, `position`?, `time`?, `milliseconds`? | `race_id` → `races.race_id`, `driver_id` → `drivers.driver_id` | composite `ix_lap_times_race_driver` on `(race_id, driver_id)` |

`?` = nullable column.

**Application Table** (1 table, managed by the app):

| Table | PK | Columns | Notes |
|-------|-----|---------|-------|
| `users` | `id` (INT, auto) | `username` (unique, indexed), `email` (unique, indexed), `hashed_password`, `role` (default `"user"`), `created_at` (auto, `server_default=now()`), `updated_at` (auto, `onupdate=now()`) | Not touched by CSV import; passwords hashed via `passlib[bcrypt]` (pinned `bcrypt==4.0.1`) |

### Key Relationships (ER)

```
seasons ──1:N──→ races ──1:N──→ results ──N:1──→ drivers
                   │               │                  │
                   │               ├──N:1──→ constructors
                   │               └──N:1──→ status
                   ├──1:N──→ qualifying
                   ├──1:N──→ pit_stops ──N:1──→ drivers
                   └──1:N──→ lap_times ──N:1──→ drivers
circuits ──1:N──→ races
```

### Design Notes

- **PitStop & LapTime** use surrogate autoincrement PKs. Natural key would be `(race_id, driver_id, stop/lap)` but ORM ergonomics favour the surrogate key.
- **`Result.position`** is `Integer` (nullable) — DNF/DNS drivers have `NULL` position. Safe to compare with `== 1` directly.
- **No Alembic**: schema changes require either manual `ALTER TABLE` or a full re-import of F1 data tables. The `users` table is preserved across re-imports.
- **Test DB**: tests use SQLite in-memory (`sqlite://` with `StaticPool`) — no PostgreSQL needed for testing.

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

## Testing

66 integration tests using **SQLite in-memory** database (no PostgreSQL needed). Tests live in `tests/` with a shared `conftest.py`.

### Test Infrastructure (`tests/conftest.py`)

- **SQLite + StaticPool**: `create_engine("sqlite://", poolclass=StaticPool)` ensures a single shared connection so `create_all` tables are visible to all sessions within a test.
- **`PRAGMA foreign_keys=ON`**: enabled via SQLAlchemy `event.listens_for(engine, "connect")` since SQLite disables FK enforcement by default.
- **Dependency override**: `app.dependency_overrides[get_db]` redirects all routes to the test session. Tables are created before each test and dropped after (`autouse` fixture).
- **Auth fixtures**: `test_user` / `admin_user` create users directly in the DB; `auth_headers` / `admin_headers` generate JWT Bearer tokens for authenticated requests.
- **`seed_data` fixture**: inserts a minimal F1 dataset (3 drivers, 3 constructors, 2 circuits, 3 races, 8 results, qualifying, pit stops) for integration tests that need populated data.

### Test Structure

| File | Count | Covers |
|------|-------|--------|
| `test_auth.py` | 11 | Register (success, duplicate username/email, validation), Login (success, wrong password, nonexistent), Token (no token, invalid token, role 403) |
| `test_drivers.py` | 15 | List (empty, pagination, nationality filter, search, sort), Get (found, 404), Create (success, duplicate 409, no auth 401), Update (success, 404, empty 400, no auth), Delete (success, 404, FK guard 409, non-admin 403) |
| `test_circuits.py` | 13 | CRUD + list with stats + detail with race history + FK guard on delete + auth/admin checks |
| `test_constructors.py` | 12 | CRUD + list with stats + detail with career summary + FK guard on delete + auth/admin checks |
| `test_analytics.py` | 10 | Career stats, leaderboard (points/wins/season), pit stop analysis, circuit history + 404 paths |

### Coverage (77% overall)

High coverage: `auth.py` 100%, `drivers.py` 92%, `circuits.py` 92%, `constructors.py` 89%, `analytics.py` 66%.
Low coverage: `advanced_analytics.py` 19% — `win-probability`, `performance-summary`, `teammate-battle` endpoints are not yet tested.

### bcrypt Compatibility

`passlib[bcrypt]` requires `bcrypt<4.1`. Version 4.1+ changed its API and breaks passlib's internal bug-detection routine. Pinned `bcrypt==4.0.1` in `requirements.txt`.

## Deployment (Render)

Deployed on Render with `render.yaml` blueprint (web service + PostgreSQL).

### Render-specific Adaptations

- **`database.py` URL fix**: Render provides `DATABASE_URL` with `postgres://` prefix, but SQLAlchemy 2.0+ requires `postgresql://`. Auto-replaced at startup.
- **`render.yaml`**: Build and start commands run directly from the repo root.
- **Environment variables**: `DATABASE_URL` (from Render DB), `SECRET_KEY` (auto-generated), `DEBUG=false`, `PYTHON_VERSION=3.12.2`.

### Data Import on Render

CSV files are in `.gitignore` (`data/*.csv`) and won't be on Render. To populate the database, connect from local machine using Render's External Connection String:
```bash
DATABASE_URL="<Render External URL>" python -m data.import_csv
```

### Render Free Tier Limitations

- PostgreSQL expires after 90 days (manual renewal required).
- Web service sleeps after 15 min of inactivity; first request has ~30-50s cold start.

