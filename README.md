# F1 Insight API 🏎️

A comprehensive Formula 1 historical data analysis RESTful API built with FastAPI, SQLAlchemy, and PostgreSQL.

## Features

- **CRUD Operations**: Full Create, Read, Update, Delete for drivers, constructors, and circuits
- **Analytics Endpoints**: Career statistics, season progressions, driver comparisons, pit stop analysis, circuit history
- **Advanced Analytics**: Win probability prediction, performance ratings, teammate battles, leaderboards
- **JWT Authentication**: Secure endpoints with role-based access control (user/admin)
- **Auto-generated Documentation**: Interactive Swagger UI and ReDoc
- **Data Source**: Ergast F1 Dataset (1950–2024), application models 11 tables from 14 source CSVs

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 14+ |
| Auth | JWT (python-jose) + passlib[bcrypt] |
| Testing | pytest + FastAPI TestClient (SQLite in-memory) |

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+

### Setup

```bash
# Clone the repository
git clone https://github.com/ZhenshuoWu/year3_web_cw1.git
cd year3_web_cw1

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create database
createdb f1_insight

# Configure environment (required — replace YOUR_USERNAME with your PostgreSQL user)
cp .env.example .env
# Then edit .env:
#   DATABASE_URL=postgresql://YOUR_USERNAME@localhost:5432/f1_insight
#   SECRET_KEY=your-secret-key

# Import F1 data
python -m data.import_csv

# Run the server
uvicorn app.main:app --reload
```

### Access
- API Root: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Testing

```bash
# Run tests (no PostgreSQL needed — uses SQLite in-memory)
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

## API Documentation

- **Interactive docs** (live server): [Swagger UI](https://f1-insight-api.onrender.com/docs) | [ReDoc](https://f1-insight-api.onrender.com/redoc)
- **OpenAPI specification**: [`docs/openapi.json`](docs/openapi.json) — machine-readable schema, can be imported into Postman or Swagger Editor
- **API documentation PDF**: [`F1 Insight API.pdf`](F1%20Insight%20API.pdf) — submission-friendly exported reference document

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |

### Drivers (CRUD)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/drivers` | List drivers (paginated, filterable, sortable) |
| GET | `/api/v1/drivers/{id}` | Get driver details |
| POST | `/api/v1/drivers` | Create driver (auth required) |
| PUT | `/api/v1/drivers/{id}` | Update driver (auth required) |
| DELETE | `/api/v1/drivers/{id}` | Delete driver (admin only) |

### Circuits (CRUD)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/circuits` | List circuits with race stats |
| GET | `/api/v1/circuits/{id}` | Circuit detail with recent winners |
| POST | `/api/v1/circuits` | Create circuit (auth required) |
| PUT | `/api/v1/circuits/{id}` | Update circuit (auth required) |
| DELETE | `/api/v1/circuits/{id}` | Delete circuit (admin only) |

### Constructors (CRUD)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/constructors` | List constructors with points and wins |
| GET | `/api/v1/constructors/{id}` | Constructor detail with top drivers |
| POST | `/api/v1/constructors` | Create constructor (auth required) |
| PUT | `/api/v1/constructors/{id}` | Update constructor (auth required) |
| DELETE | `/api/v1/constructors/{id}` | Delete constructor (admin only) |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/drivers/{id}/career-stats` | Driver career statistics |
| GET | `/api/v1/analytics/drivers/{id}/season-progression` | Season points progression |
| GET | `/api/v1/analytics/drivers/compare` | Head-to-head driver comparison |
| GET | `/api/v1/analytics/races/{id}/pit-stop-analysis` | Pit stop strategy analysis |
| GET | `/api/v1/analytics/circuits/{id}/history` | Circuit historical statistics |

### Advanced Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/win-probability` | Win probability prediction |
| GET | `/api/v1/analytics/drivers/{id}/performance-summary` | Multi-dimensional performance rating |
| GET | `/api/v1/analytics/teammate-battle` | Teammate head-to-head comparison |
| GET | `/api/v1/analytics/leaderboard` | Dynamic leaderboard by various metrics |

## Project Structure

```
year3_web_cw1/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management (pydantic-settings)
│   ├── database.py          # Database connection and session
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic validation schemas
│   ├── routers/             # API route handlers
│   └── utils/               # Authentication helpers
├── tests/                   # Integration test suite (66 tests)
├── data/                    # CSV data and import script
├── requirements.txt
└── README.md
```

## Data Source

This API uses the [Ergast F1 Dataset (Kaggle mirror)](https://www.kaggle.com/datasets/jtrotman/formula-1-race-data) covering Formula 1 race data from 1950 to 2024. The repository ships 14 CSV files; 10 are imported into the database, while the remaining 4 (`driver_standings`, `constructor_standings`, `constructor_results`, `sprint_results`) are not imported — their data is derived at query time via aggregation. Together with the application `users` table, the database schema consists of 11 tables. Schema is managed directly through SQLAlchemy model definitions — no migration tool is used.

## License

This project is developed for academic purposes as part of COMP3011 Web Services coursework at the University of Leeds.
