# F1 Insight API 🏎️

A comprehensive Formula 1 historical data analysis RESTful API built with FastAPI, SQLAlchemy, and PostgreSQL.

## Features

- **CRUD Operations**: Full Create, Read, Update, Delete for drivers, constructors, circuits, and races
- **Analytics Endpoints**: Career statistics, season progressions, driver comparisons, pit stop analysis
- **JWT Authentication**: Secure endpoints with role-based access control (user/admin)
- **Auto-generated Documentation**: Interactive Swagger UI and ReDoc
- **Data Source**: Ergast F1 Dataset (1950–2024) with 8 normalised database tables

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 14+ |
| Migration | Alembic |
| Auth | JWT (python-jose) |
| Testing | pytest + httpx |

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/f1-insight-api.git
cd f1-insight-api

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create database
createdb f1_insight

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Import F1 data
python -m data.import_csv

# Run the server
uvicorn app.main:app --reload
```

### Access
- API Root: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |

### Drivers (CRUD)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/drivers` | List drivers (paginated, filterable) |
| GET | `/api/v1/drivers/{id}` | Get driver details |
| POST | `/api/v1/drivers` | Create driver (auth required) |
| PUT | `/api/v1/drivers/{id}` | Update driver (auth required) |
| DELETE | `/api/v1/drivers/{id}` | Delete driver (admin only) |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/drivers/{id}/career-stats` | Driver career statistics |
| GET | `/api/v1/analytics/drivers/{id}/season-progression` | Season points progression |
| GET | `/api/v1/analytics/drivers/compare` | Head-to-head driver comparison |
| GET | `/api/v1/analytics/races/{id}/pit-stop-analysis` | Pit stop strategy analysis |
| GET | `/api/v1/analytics/circuits/{id}/history` | Circuit historical statistics |

## Project Structure

```
f1-insight-api/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic validation schemas
│   ├── routers/             # API route handlers
│   ├── services/            # Business logic layer
│   ├── middleware/           # Rate limiting, logging
│   └── utils/               # Authentication, helpers
├── tests/                   # Test suite
├── data/                    # CSV data and import scripts
├── requirements.txt
└── README.md
```

## Data Source

This API uses the [Ergast F1 Dataset](https://www.kaggle.com/datasets/) covering Formula 1 race data from 1950 to 2024. The dataset is imported into a normalised PostgreSQL schema with 8 interconnected tables.

## License

This project is developed for academic purposes as part of COMP3011 Web Services coursework at the University of Leeds.
