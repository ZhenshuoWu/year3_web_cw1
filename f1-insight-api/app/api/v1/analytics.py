from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analytics import (
    CircuitHistoryResponse,
    DriverCareerStatsResponse,
    DriverCompareResponse,
    DriverSeasonProgressionResponse,
    PitStopAnalysisResponse,
)
from app.services import analytics_service

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/drivers/{driver_id}/career-stats", response_model=DriverCareerStatsResponse)
def get_driver_career_stats(driver_id: int, db: Session = Depends(get_db)):
    """
    Get comprehensive career statistics for a driver.
    Includes: total races, wins, podiums, poles, points, win rate, etc.
    """
    return analytics_service.get_driver_career_stats(db, driver_id)


@router.get("/drivers/{driver_id}/season-progression", response_model=DriverSeasonProgressionResponse)
def get_driver_season_progression(
    driver_id: int,
    season: int = Query(..., description="Season year"),
    db: Session = Depends(get_db)
):
    """
    Get a driver's points accumulation across a season.
    Returns round-by-round cumulative points for charting progression curves.
    """
    return analytics_service.get_driver_season_progression(db, driver_id, season)


@router.get("/drivers/compare", response_model=DriverCompareResponse)
def compare_drivers(
    d1: int = Query(..., description="First driver ID"),
    d2: int = Query(..., description="Second driver ID"),
    season: Optional[int] = Query(None, description="Optional season filter"),
    db: Session = Depends(get_db)
):
    """
    Head-to-head comparison between two drivers.
    Compares wins, points, podiums, and direct race encounters.
    """
    return analytics_service.compare_drivers(db, d1, d2, season)


@router.get("/races/{race_id}/pit-stop-analysis", response_model=PitStopAnalysisResponse)
def get_pit_stop_analysis(race_id: int, db: Session = Depends(get_db)):
    """
    Analyse pit stop strategies and their impact on race results for a given race.
    Shows correlation between number of stops, pit duration, and final position.
    """
    return analytics_service.get_pit_stop_analysis(db, race_id)


@router.get("/circuits/{circuit_id}/history", response_model=CircuitHistoryResponse)
def get_circuit_history(circuit_id: int, db: Session = Depends(get_db)):
    """
    Get historical statistics for a circuit.
    Includes: all races held, average finishers, most successful drivers.
    """
    return analytics_service.get_circuit_history(db, circuit_id)
