from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, drivers, analytics

settings = get_settings()

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## F1 Insight API 🏎️

    A comprehensive Formula 1 historical data analysis API providing:

    - **CRUD Operations**: Manage drivers, constructors, circuits, and races
    - **Analytics**: Career stats, season progressions, head-to-head comparisons
    - **Strategy Analysis**: Pit stop strategies, circuit history, performance trends

    Data sourced from the Ergast F1 Dataset (1950–2024).
    """,
    docs_url="/docs",
    redoc_url="/redoc",
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
