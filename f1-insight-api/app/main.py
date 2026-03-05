from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.logging import setup_logging
from app.core.settings import get_settings
from app.database import engine, Base
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware

settings = get_settings()

# Create all tables
Base.metadata.create_all(bind=engine)

def create_app() -> FastAPI:
    setup_logging(settings.DEBUG)

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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware, max_body_chars=settings.LOG_BODY_MAX_CHARS)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )

    app.include_router(api_router)

    @app.get("/", tags=["Root"])
    def root():
        return {
            "message": "Welcome to F1 Insight API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "redoc": "/redoc",
        }

    @app.get("/health", tags=["Root"])
    def health_check():
        return {"status": "healthy"}

    return app


app = create_app()
