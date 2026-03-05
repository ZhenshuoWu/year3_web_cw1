from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analytics import (
    LeaderboardResponse,
    PerformanceSummaryResponse,
    TeammateBattleResponse,
    WinProbabilityResponse,
)
from app.services import advanced_analytics_service

router = APIRouter(prefix="/api/v1/analytics", tags=["Advanced Analytics"])


@router.get("/win-probability", response_model=WinProbabilityResponse)
def get_win_probability(
    driver_id: int = Query(..., description="Driver ID"),
    circuit_id: int = Query(..., description="Circuit ID"),
    db: Session = Depends(get_db),
):
    return advanced_analytics_service.get_win_probability(db, driver_id, circuit_id)


@router.get("/drivers/{driver_id}/performance-summary", response_model=PerformanceSummaryResponse)
def get_performance_summary(
    driver_id: int,
    season: Optional[int] = Query(None, description="Filter by season (default: all-time)"),
    db: Session = Depends(get_db),
):
    return advanced_analytics_service.get_performance_summary(db, driver_id, season)


@router.get("/teammate-battle", response_model=TeammateBattleResponse)
def get_teammate_battle(
    driver_id: int = Query(..., description="Driver ID"),
    season: int = Query(..., description="Season year"),
    db: Session = Depends(get_db),
):
    return advanced_analytics_service.get_teammate_battle(db, driver_id, season)


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    season: Optional[int] = Query(None, description="Season year (default: all-time)"),
    metric: str = Query("points", description="Ranking metric: 'points', 'wins', 'podiums', 'win_rate'"),
    limit: int = Query(20, ge=1, le=100, description="Number of drivers to return"),
    db: Session = Depends(get_db),
):
    return advanced_analytics_service.get_leaderboard(db, season, metric, limit)
