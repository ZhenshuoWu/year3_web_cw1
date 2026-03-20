# F1 Insight API — Technical Report

**Module:** COMP3011 — Web Services API Development
**Student:** [Insert Name and Student ID]
**Date:** March 2026

**Deliverables:**

- GitHub Repository: [Insert Public GitHub Link]
- Live API Documentation: https://f1-insight-api.onrender.com/docs
- Presentation Slides: [Insert Slides Link]

---

## 1. Design and Architectural Choices

### 1.1 Technology Stack Overview

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.12 |
| Web Framework | FastAPI | 0.115.0 |
| ORM | SQLAlchemy | 2.0.35 |
| Database | PostgreSQL | (local dev + Render production) |
| Authentication | JWT via python-jose + passlib[bcrypt] | — |
| Data Import | pandas | 2.2.3 |
| Testing | pytest + httpx | 8.3.3 / 0.27.2 |
| Deployment | Render (Web Service + Managed PostgreSQL) | — |

[Insert Architecture Diagram Here — suggested: a layered diagram showing Client → FastAPI Router → SQLAlchemy ORM → PostgreSQL, with JWT auth as a cross-cutting concern]

### 1.2 Justification of Choices

**Python and FastAPI.** Python was selected for its mature data processing ecosystem (pandas for CSV import, SQLAlchemy for ORM) and rapid development cycle. FastAPI was chosen over alternatives such as Flask and Django REST Framework for three reasons: (1) automatic OpenAPI/Swagger documentation generation from type hints, which directly satisfies the coursework's API documentation requirement; (2) built-in request validation via Pydantic, eliminating boilerplate; and (3) native dependency injection (`Depends()`), which enabled clean separation of database sessions and authentication logic without a manual service layer.

**PostgreSQL (Relational Database).** The Ergast F1 dataset is inherently relational — races reference circuits and seasons via foreign keys, results reference races, drivers, and constructors, and lap times reference both races and drivers. PostgreSQL was chosen over NoSQL alternatives because the analytics endpoints rely heavily on multi-table `JOIN` and `GROUP BY` aggregations (e.g., computing career statistics across the `results`, `races`, and `drivers` tables). A document store such as MongoDB would have required either data denormalisation — introducing update anomalies across 26,000+ results — or application-level joins that would negate the performance benefits of a database engine. PostgreSQL's query planner handles these aggregations natively.

**SQLAlchemy 2.0 (ORM).** SQLAlchemy provides declarative model definitions that serve as a single source of truth for both schema creation and query construction. The 2.0 API was chosen for its improved type safety and explicit session management, which aligns with FastAPI's dependency injection pattern. Schema is managed entirely through model definitions (`Base.metadata.create_all()`), deliberately avoiding migration tools like Alembic to reduce complexity for a dataset that is imported in bulk rather than evolved incrementally.

**JWT Authentication.** Stateless token-based authentication was chosen over session-based auth to align with RESTful principles. The API issues a signed JWT on login, and protected endpoints verify the token via a FastAPI dependency (`get_current_user`). Role-based access control distinguishes regular users (who can create and update records) from admins (who can delete records), reflecting a realistic multi-tenant API design.

### 1.3 API Design Highlights

The API exposes 6 router groups under a versioned prefix (`/api/v1/`): Authentication, Drivers, Circuits, Constructors, Analytics, and Advanced Analytics. Full CRUD is supported for the core entity endpoints, while the analytics endpoints are read-only and compute all statistics from raw race data — no pre-aggregated standings tables are used, demonstrating real-time query capability.

**Multi-dimensional sorting system.** A key design feature is the `sort_by` parameter on list endpoints, supporting five modes: `popularity` (all-time points), `recent` (latest season points), `wins` (career wins), `newest`, and `oldest`. This was inspired by content recommendation patterns in consumer platforms (e.g., video streaming services), where users expect multiple ranking perspectives on the same dataset. I proposed this idea and iteratively developed it from a simple ascending/descending toggle into a 5-option intelligent ranking system that performs real-time aggregation across the `drivers`, `results`, and `races` tables. The `recent` sort dynamically queries the latest season and uses an `outerjoin` subquery so that historical drivers (e.g., retired drivers with no current-season data) appear with zero points rather than being silently dropped.

I specifically chose single-season data for the `recent` metric after analysing whether 1, 3, or 5 seasons would be more appropriate. Single-season maximises differentiation from the all-time `popularity` metric — a retired driver like Schumacher ranks highly in popularity but disappears from recent, giving users genuinely different information from each sort option. A 3- or 5-year window would have overlapped too heavily with the all-time ranking, reducing the utility of having separate sort modes.

**Win probability model.** The advanced analytics endpoints include a win probability prediction that combines four weighted factors: historical performance at a specific circuit, recent form (last 5 races), grid-to-finish conversion rate, and career baseline. This endpoint was prioritised first among the four advanced analytics options because it directly addresses the coursework brief's mention of "win probabilities," demonstrating alignment between implementation decisions and assessment criteria.

---

## 2. Data Sources and References

### 2.1 Primary Dataset

The API is powered by the **Ergast Motor Racing Developer API dataset** (http://ergast.com/mrd/), a comprehensive Formula 1 historical database covering every season from 1950 to 2024. Ten CSV files are imported, totalling approximately 26,000+ race results across 850+ drivers, 210+ constructors, and 77 circuits.

| CSV File | Records (approx.) | Description |
|----------|-------------------|-------------|
| `seasons.csv` | 75 | Season years and Wikipedia URLs |
| `circuits.csv` | 77 | Circuit metadata (location, coordinates) |
| `drivers.csv` | 859 | Driver biographical data |
| `constructors.csv` | 212 | Constructor/team information |
| `status.csv` | 139 | Race finish status codes |
| `races.csv` | 1,125 | Race events with dates and session times |
| `results.csv` | 26,000+ | Individual race results |
| `qualifying.csv` | 10,000+ | Qualifying session times |
| `pit_stops.csv` | 10,000+ | Pit stop timings (available from 2011) |
| `lap_times.csv` | 550,000+ | Individual lap times (available from 1996) |

Four additional CSV files (`driver_standings`, `constructor_standings`, `constructor_results`, `sprint_results`) were intentionally excluded because their data is derived at query time via aggregation in the analytics endpoints, avoiding data redundancy.

### 2.2 Libraries and References

- **FastAPI** (Ramírez, 2018): https://fastapi.tiangolo.com/
- **SQLAlchemy** (Bayer, 2012): https://www.sqlalchemy.org/
- **Pydantic** (Colvin, 2017): https://docs.pydantic.dev/
- **pandas** (McKinney, 2010): https://pandas.pydata.org/
- **python-jose** (Melvill, 2015): JWT implementation for Python
- **passlib** (Warren, 2008): Password hashing library with bcrypt backend
- **Render** (Render, 2019): Cloud platform for deployment — https://render.com/

---

## 3. Challenges, Testing, and Reflection

### 3.1 Technical Challenges

**N+1 query problem.** The initial implementation of the `compare_drivers` and `get_pit_stop_analysis` endpoints contained N+1 query patterns — for each driver being compared, a separate database query was issued for their constructor name and race details. With the full dataset, comparing two drivers with 300+ races each generated hundreds of individual queries. The fix involved replacing per-row lookups with bulk `.in_()` fetches that load all required data in a single query, then using Python dict lookups for O(1) access. This reduced query counts from O(n) to O(1) per endpoint call.

[Insert Before/After Query Count Comparison Diagram Here — suggested: a simple bar chart showing queries-per-request before and after optimisation]

**Pit stop outlier filtering.** The pit stop analysis endpoint initially produced misleading statistics because red-flag periods (where cars are stationary for extended durations) were included in average pit stop time calculations. After inspecting the data distribution, a threshold of 45,000 milliseconds was established to filter out anomalous stops. Additionally, the median was chosen over the mean as the central tendency measure, since pit stop durations exhibit right-skewed distributions where a single outlier can distort the average significantly.

**SQLite vs PostgreSQL testing divergence.** The test suite uses SQLite in-memory databases for speed and zero-configuration setup, while production runs on PostgreSQL. This introduced subtle compatibility issues: SQLite disables foreign key enforcement by default (requiring explicit `PRAGMA foreign_keys=ON` per connection), lacks native support for some PostgreSQL-specific types and functions, and handles `NULL` sorting differently. These were resolved by: (1) attaching a SQLAlchemy event listener to enable foreign keys on every SQLite connection; (2) using `StaticPool` to ensure a single shared connection (so `create_all` tables are visible across sessions); and (3) writing ORM-level queries that abstract away dialect differences rather than using raw SQL.

**bcrypt version incompatibility.** The `passlib` library's bcrypt backend broke silently with `bcrypt>=4.1` due to an internal API change. Debugging this required tracing through passlib's source code to identify the version constraint, ultimately resolved by pinning `bcrypt==4.0.1` in `requirements.txt`.

### 3.2 Testing Approach

The API is validated by **66 integration tests** across 5 test files, achieving **77% overall code coverage**. Tests use FastAPI's `TestClient` (backed by httpx) to make real HTTP requests against the application, with dependency injection overriding the database session to use an isolated SQLite instance.

| Test File | Tests | Coverage | Focus Area |
|-----------|-------|----------|------------|
| `test_auth.py` | 11 | 100% | Registration, login, JWT validation, role-based access |
| `test_drivers.py` | 15 | 92% | CRUD, pagination, filtering, sorting, auth guards |
| `test_circuits.py` | 13 | 92% | CRUD, aggregated stats, race history, FK constraints |
| `test_constructors.py` | 12 | 89% | CRUD, career summaries, top drivers, auth/admin checks |
| `test_analytics.py` | 10 | 66% | Career stats, leaderboards, pit stop analysis, circuit history |

Key testing patterns include: a `seed_data` fixture that inserts a minimal but realistic F1 dataset (3 drivers, 3 constructors, 2 circuits, 3 races, 8 results) for analytics tests; separate `auth_headers` and `admin_headers` fixtures for testing role-based access; and `autouse` fixtures that create and drop all tables between tests to ensure isolation.

### 3.3 Reflection and Lessons Learned

The most significant lesson was understanding the tension between **computational expressiveness and query performance**. Computing analytics from raw data (rather than pre-aggregated tables) provides maximum flexibility but requires careful attention to query design. The N+1 problem taught me that ORM convenience can mask serious performance issues that only surface at scale.

The SQLite/PostgreSQL divergence highlighted the importance of testing against the production database engine in a CI pipeline — a gap I would address in future iterations. Similarly, the bcrypt compatibility issue reinforced the importance of pinning dependency versions and understanding transitive dependencies.

---

## 4. Limitations and Future Development

### 4.1 Current Limitations

- **No Alembic migrations.** Schema changes currently require either manual `ALTER TABLE` statements or a full re-import of F1 data tables. This is acceptable for a static historical dataset but would not scale to a production system with evolving requirements.
- **Test coverage gap.** The `advanced_analytics.py` module (win probability, performance summary, teammate battle) has only 19% test coverage. These endpoints involve complex multi-factor calculations that require more sophisticated seed data to test effectively.
- **No caching layer.** Analytics queries that aggregate over the full dataset (e.g., all-time leaderboards) execute the full computation on every request. A caching strategy (e.g., Redis with TTL-based invalidation) would significantly improve response times for repeated queries.
- **Cold start latency.** The Render free tier suspends the web service after 15 minutes of inactivity, resulting in a 30–50 second cold start on the first request. This is a hosting constraint rather than an application issue.
- **CORS configuration.** The current `allow_origins=["*"]` setting is permissive for development but would need to be restricted in a production environment to prevent cross-origin abuse.

### 4.2 Future Development

- **Rate limiting and API keys.** The `slowapi` dependency is included but could be expanded into a full API key management system with per-user quotas.
- **Real-time data integration.** Connecting to a live F1 data feed (e.g., the OpenF1 API) would keep the dataset current without manual CSV imports.
- **GraphQL layer.** Adding a GraphQL endpoint alongside the REST API would allow clients to request precisely the fields they need, reducing over-fetching on the analytics endpoints that return large nested objects.
- **WebSocket for live race tracking.** A WebSocket endpoint could push lap-by-lap updates during live races, extending the API from historical analysis to real-time telemetry.
- **Containerisation.** Packaging the application with Docker would eliminate environment discrepancies (such as the bcrypt version issue) and simplify deployment across different platforms.

---

## 5. Generative AI Declaration and Analysis

### 5.1 Declaration of Use

Generative AI tools — specifically **Claude Code** (Anthropic's CLI-based coding assistant) — were used extensively throughout the development of this project. The following areas involved GenAI assistance:

| Area | GenAI Role | My Contribution |
|------|-----------|-----------------|
| Dataset discovery | Suggested Ergast F1 dataset | Evaluated suitability and scope |
| Data import script | Generated `import_csv.py` with column mappings | Defined import order, identified FK dependencies |
| Boilerplate code | Generated initial router, model, and schema files | Designed API structure, endpoint naming, response shapes |
| Sorting system | Implemented SQL queries for each sort mode | Proposed the multi-dimensional sort concept; determined single-season for `recent` after data analysis |
| Analytics endpoints | Implemented aggregation queries | Prioritised Win Probability first to align with brief; questioned data range choices |
| Debugging | Identified N+1 queries, bcrypt incompatibility | Reported symptoms, validated fixes against production data |
| Testing | Generated test structure and seed data fixtures | Defined test scenarios, verified edge cases (FK guard, 404 paths) |
| Deployment | Configured `render.yaml` and database URL adaptation | Managed Render setup, environment variables, data import |

### 5.2 Analysis of GenAI Usage

GenAI served primarily as an **implementation accelerator** — translating design decisions into working code faster than manual implementation. However, the critical design decisions remained human-driven:

1. **The multi-dimensional sorting concept** originated from my observation of content recommendation systems in video streaming platforms. I proposed this to Claude and we iteratively developed it from a simple toggle into a 5-option system. The key insight — that single-season data maximises differentiation from all-time rankings — came from my analysis of how retired drivers (e.g., Schumacher ranking #2 in popularity but absent from recent) would behave under different time windows.

2. **Feature prioritisation** was driven by systematic alignment with assessment criteria. When presented with four advanced analytics endpoint options, I chose Win Probability as the first priority because the coursework brief explicitly mentions "win probabilities." This was a deliberate decision to maximise mark-relevant coverage rather than implementing endpoints in arbitrary order.

3. **Data quality decisions** such as the pit stop outlier threshold (45,000ms) and the choice of median over mean required domain understanding that GenAI suggested but I validated against the actual data distribution.

The primary risk of GenAI-assisted development was **over-reliance on generated code without understanding the underlying query semantics**. I mitigated this by reviewing all generated SQL queries, running `EXPLAIN ANALYZE` on complex aggregations, and manually verifying results against known F1 statistics. The N+1 query fix, for example, was first identified by Claude but I confirmed the performance improvement by comparing query counts before and after the optimisation.

### 5.3 Conversation Logs

Full conversation logs with Claude Code are attached as an appendix to this submission.

[Insert Appendix Reference — attach exported Claude Code conversation logs]

---

## References

- Ergast Developer API. (2024). *Motor Racing Data*. Available at: http://ergast.com/mrd/
- FastAPI. (2018). *FastAPI Documentation*. Available at: https://fastapi.tiangolo.com/
- SQLAlchemy. (2012). *SQLAlchemy Documentation*. Available at: https://www.sqlalchemy.org/
- Pydantic. (2017). *Pydantic Documentation*. Available at: https://docs.pydantic.dev/
- Render. (2019). *Render Cloud Platform*. Available at: https://render.com/
