from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, drivers, analytics, advanced_analytics
from app.routers import circuits, constructors

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (not at import time)
    Base.metadata.create_all(bind=engine)
    yield


tags_metadata = [
    {
        "name": "Root",
        "description": "Health check and API information.",
    },
    {
        "name": "Authentication",
        "description": "User registration and JWT-based login. Register an account and login to receive a Bearer token for protected endpoints.",
    },
    {
        "name": "Drivers",
        "description": "CRUD operations for F1 drivers. Supports pagination, nationality filter, name search, and sorting by newest/oldest/popularity/recent/wins. POST/PUT require authentication; DELETE requires admin.",
    },
    {
        "name": "Circuits",
        "description": "CRUD operations for F1 circuits. List includes total races per circuit. Detail view shows the 5 most recent race winners. POST/PUT require authentication; DELETE requires admin.",
    },
    {
        "name": "Constructors",
        "description": "CRUD operations for F1 constructors (teams). List includes total points and wins. Detail view shows career summary and top 5 drivers. POST/PUT require authentication; DELETE requires admin.",
    },
    {
        "name": "Analytics",
        "description": "Core F1 data analysis: career stats, season progression curves, head-to-head driver comparisons, pit stop strategy analysis, and circuit historical records. All computed from raw race data (no pre-aggregated tables).",
    },
    {
        "name": "Advanced Analytics",
        "description": "Advanced analytical models: win probability prediction (4-factor weighted model), multi-dimensional performance ratings (0-100), teammate head-to-head battle comparisons, and dynamic leaderboards by various metrics.",
    },
]

app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## F1 Insight API

A comprehensive Formula 1 historical data analysis API covering **every season from 1950 to 2024**.

### Features

- **CRUD Operations** - Manage drivers, constructors, and circuits with full pagination, filtering, and sorting
- **Career Analytics** - Lifetime stats, season progression curves, head-to-head driver comparisons
- **Strategy Analysis** - Pit stop strategies, circuit history, performance trends
- **Advanced Models** - Win probability prediction, multi-dimensional performance ratings, teammate battles, leaderboards

### Authentication

Protected endpoints require a JWT Bearer token. Register via `POST /api/v1/auth/register`, then login via `POST /api/v1/auth/login` to receive your token.

### Data Source

[Ergast F1 Dataset (Kaggle mirror)](https://www.kaggle.com/datasets/jtrotman/formula-1-race-data) - 10 tables, 26,000+ race results, 850+ drivers.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(drivers.router)
app.include_router(analytics.router)
app.include_router(advanced_analytics.router)
app.include_router(circuits.router)
app.include_router(constructors.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to F1 Insight API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "healthy"}
