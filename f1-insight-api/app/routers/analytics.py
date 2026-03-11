from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
from typing import Optional
from app.database import get_db
from app.models import Driver, Result, Race, Constructor, PitStop, Qualifying, Status

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/drivers/{driver_id}/career-stats")
def get_driver_career_stats(driver_id: int, db: Session = Depends(get_db)):
    """
    Get comprehensive career statistics for a driver.
    Includes: total races, wins, podiums, poles, points, win rate, etc.
    """
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    results = db.query(Result).filter(Result.driver_id == driver_id).all()
    if not results:
        raise HTTPException(status_code=404, detail="No race data found for this driver")

    total_races = len(results)
    wins = sum(1 for r in results if r.position == 1)
    podiums = sum(1 for r in results if r.position and r.position <= 3)
    poles = sum(1 for r in results if r.grid == 1)
    total_points = sum(r.points for r in results if r.points)
    dnfs = sum(1 for r in results if r.position is None or r.position_text == "R")
    best_finish = min((r.position for r in results if r.position), default=None)

    # Get distinct constructors (teams driven for)
    constructor_ids = db.query(Result.constructor_id).filter(
        Result.driver_id == driver_id
    ).distinct().all()
    teams = db.query(Constructor.name).filter(
        Constructor.constructor_id.in_([c[0] for c in constructor_ids])
    ).all()

    # Get season range
    race_ids = [r.race_id for r in results]
    seasons = db.query(Race.year).filter(Race.race_id.in_(race_ids)).distinct().order_by(Race.year).all()

    return {
        "driver": {
            "id": driver.driver_id,
            "name": f"{driver.forename} {driver.surname}",
            "nationality": driver.nationality
        },
        "career": {
            "total_races": total_races,
            "wins": wins,
            "podiums": podiums,
            "pole_positions": poles,
            "total_points": round(total_points, 1),
            "dnfs": dnfs,
            "best_finish": best_finish,
            "win_rate": round(wins / total_races * 100, 2) if total_races > 0 else 0,
            "podium_rate": round(podiums / total_races * 100, 2) if total_races > 0 else 0,
        },
        "teams": [t[0] for t in teams],
        "seasons": [s[0] for s in seasons]
    }


@router.get("/drivers/{driver_id}/season-progression")
def get_driver_season_progression(
    driver_id: int,
    season: int = Query(..., description="Season year"),
    db: Session = Depends(get_db)
):
    """
    Get a driver's points accumulation across a season.
    Returns round-by-round cumulative points for charting progression curves.
    """
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    results = (
        db.query(Result, Race)
        .join(Race, Result.race_id == Race.race_id)
        .filter(Result.driver_id == driver_id, Race.year == season)
        .order_by(Race.round)
        .all()
    )

    if not results:
        raise HTTPException(status_code=404, detail="No data for this driver in the specified season")

    cumulative_points = 0
    progression = []
    for result, race in results:
        cumulative_points += result.points or 0
        progression.append({
            "round": race.round,
            "race_name": race.name,
            "position": result.position,
            "points_scored": result.points or 0,
            "cumulative_points": round(cumulative_points, 1)
        })

    return {
        "driver": f"{driver.forename} {driver.surname}",
        "season": season,
        "total_points": round(cumulative_points, 1),
        "rounds": progression
    }


@router.get("/drivers/compare")
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
    driver1 = db.query(Driver).filter(Driver.driver_id == d1).first()
    driver2 = db.query(Driver).filter(Driver.driver_id == d2).first()
    if not driver1 or not driver2:
        raise HTTPException(status_code=404, detail="One or both drivers not found")

    def get_stats(driver_id, season_filter=None):
        query = db.query(Result).join(Race)
        query = query.filter(Result.driver_id == driver_id)
        if season_filter:
            query = query.filter(Race.year == season_filter)
        results = query.all()

        return {
            "total_races": len(results),
            "wins": sum(1 for r in results if r.position == 1),
            "podiums": sum(1 for r in results if r.position and r.position <= 3),
            "total_points": round(sum(r.points or 0 for r in results), 1),
            "dnfs": sum(1 for r in results if r.position is None),
            "avg_finish": round(
                sum(r.position for r in results if r.position) /
                max(sum(1 for r in results if r.position), 1), 2
            )
        }

    # Find races where both competed
    d1_races = set(
        r.race_id for r in db.query(Result).filter(Result.driver_id == d1).all()
    )
    d2_races = set(
        r.race_id for r in db.query(Result).filter(Result.driver_id == d2).all()
    )
    common_races = d1_races & d2_races

    # Head-to-head in common races
    # Fetch all results for both drivers in one query instead of N*2 queries
    common_results = (
        db.query(Result)
        .filter(Result.driver_id.in_([d1, d2]), Result.race_id.in_(common_races))
        .all()
    )
    result_map = {(r.race_id, r.driver_id): r for r in common_results}

    d1_ahead = 0
    d2_ahead = 0
    for race_id in common_races:
        r1 = result_map.get((race_id, d1))
        r2 = result_map.get((race_id, d2))
        if r1 and r2 and r1.position_order and r2.position_order:
            if r1.position_order < r2.position_order:
                d1_ahead += 1
            elif r2.position_order < r1.position_order:
                d2_ahead += 1

    return {
        "driver_1": {
            "name": f"{driver1.forename} {driver1.surname}",
            "stats": get_stats(d1, season)
        },
        "driver_2": {
            "name": f"{driver2.forename} {driver2.surname}",
            "stats": get_stats(d2, season)
        },
        "head_to_head": {
            "common_races": len(common_races),
            f"{driver1.surname}_ahead": d1_ahead,
            f"{driver2.surname}_ahead": d2_ahead
        },
        "season_filter": season
    }


@router.get("/races/{race_id}/pit-stop-analysis")
def get_pit_stop_analysis(race_id: int, db: Session = Depends(get_db)):
    """
    Analyse pit stop strategies and their impact on race results for a given race.
    Shows correlation between number of stops, pit duration, and final position.
    """
    race = db.query(Race).filter(Race.race_id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    pit_stops = db.query(PitStop).filter(PitStop.race_id == race_id).all()
    results = db.query(Result).filter(Result.race_id == race_id).all()

    if not pit_stops:
        raise HTTPException(status_code=404, detail="No pit stop data available for this race")

    # Group pit stops by driver
    driver_stops = {}
    for ps in pit_stops:
        if ps.driver_id not in driver_stops:
            driver_stops[ps.driver_id] = []
        driver_stops[ps.driver_id].append({
            "stop": ps.stop,
            "lap": ps.lap,
            "duration": ps.duration,
            "milliseconds": ps.milliseconds
        })

    # Fetch all drivers in one query instead of one per result
    driver_ids = [r.driver_id for r in results]
    drivers = db.query(Driver).filter(Driver.driver_id.in_(driver_ids)).all()
    driver_map = {d.driver_id: d for d in drivers}

    # Combine with results
    analysis = []
    for result in results:
        driver = driver_map.get(result.driver_id)
        stops = driver_stops.get(result.driver_id, [])
        total_pit_time = sum(s["milliseconds"] or 0 for s in stops)

        analysis.append({
            "driver": f"{driver.forename} {driver.surname}" if driver else "Unknown",
            "grid_position": result.grid,
            "final_position": result.position,
            "num_stops": len(stops),
            "total_pit_time_ms": total_pit_time,
            "stops_detail": stops
        })

    analysis.sort(key=lambda x: x["final_position"] or 999)

    # Summary statistics
    strategies = {}
    for a in analysis:
        n = a["num_stops"]
        if n not in strategies:
            strategies[n] = {"count": 0, "avg_finish": []}
        strategies[n]["count"] += 1
        if a["final_position"]:
            strategies[n]["avg_finish"].append(a["final_position"])

    strategy_summary = {
        f"{k}_stop": {
            "drivers": v["count"],
            "avg_finish_position": round(sum(v["avg_finish"]) / len(v["avg_finish"]), 1) if v["avg_finish"] else None
        }
        for k, v in sorted(strategies.items())
    }

    return {
        "race": race.name,
        "season": race.year,
        "strategy_summary": strategy_summary,
        "driver_details": analysis
    }


@router.get("/circuits/{circuit_id}/history")
def get_circuit_history(circuit_id: int, db: Session = Depends(get_db)):
    """
    Get historical statistics for a circuit.
    Includes: all races held, average finishers, most successful drivers.
    """
    from sqlalchemy import func

    circuit = db.query(Race).filter(Race.circuit_id == circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="No races found for this circuit")

    circuit_info = (
        db.query(
            Race.circuit_id,
            func.count(Race.race_id).label("total_races"),
            func.min(Race.year).label("first_race"),
            func.max(Race.year).label("last_race")
        )
        .filter(Race.circuit_id == circuit_id)
        .group_by(Race.circuit_id)
        .first()
    )

    # Most wins at this circuit
    race_ids = [r.race_id for r in db.query(Race).filter(Race.circuit_id == circuit_id).all()]
    winners = (
        db.query(
            Driver.forename, Driver.surname,
            func.count(Result.result_id).label("wins")
        )
        .join(Result, Result.driver_id == Driver.driver_id)
        .filter(Result.race_id.in_(race_ids), Result.position == 1)
        .group_by(Driver.driver_id, Driver.forename, Driver.surname)
        .order_by(desc("wins"))
        .limit(5)
        .all()
    )

    from app.models import Circuit as CircuitModel
    circuit_detail = db.query(CircuitModel).filter(CircuitModel.circuit_id == circuit_id).first()

    return {
        "circuit": {
            "name": circuit_detail.name if circuit_detail else "Unknown",
            "location": circuit_detail.location if circuit_detail else None,
            "country": circuit_detail.country if circuit_detail else None
        },
        "statistics": {
            "total_races": circuit_info.total_races,
            "first_race_year": circuit_info.first_race,
            "last_race_year": circuit_info.last_race
        },
        "most_successful_drivers": [
            {"driver": f"{w.forename} {w.surname}", "wins": w.wins}
            for w in winners
        ]
    }
