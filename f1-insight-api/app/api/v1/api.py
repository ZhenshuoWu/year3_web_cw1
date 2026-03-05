from fastapi import APIRouter

from app.api.v1 import advanced_analytics, analytics, auth, drivers

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(drivers.router)
api_router.include_router(analytics.router)
api_router.include_router(advanced_analytics.router)
