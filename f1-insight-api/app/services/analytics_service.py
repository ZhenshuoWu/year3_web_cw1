from typing import Optional

from fastapi import HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models import Circuit as CircuitModel
from app.models import Constructor, Driver, PitStop, Race, Result


def get_driver_career_stats(db: Session, driver_id: int):
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

    constructor_ids = db.query(Result.constructor_id).filter(Result.driver_id == driver_id).distinct().all()
    teams = db.query(Constructor.name).filter(Constructor.constructor_id.in_([c[0] for c in constructor_ids])).all()

    race_ids = [r.race_id for r in results]
    seasons = db.query(Race.year).filter(Race.race_id.in_(race_ids)).distinct().order_by(Race.year).all()

    return {
        "driver": {
            "id": driver.driver_id,
            "name": f"{driver.forename} {driver.surname}",
            "nationality": driver.nationality,
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
        "seasons": [s[0] for s in seasons],
    }


def get_driver_season_progression(db: Session, driver_id: int, season: int):
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
        progression.append(
            {
                "round": race.round,
                "race_name": race.name,
                "position": result.position,
                "points_scored": result.points or 0,
                "cumulative_points": round(cumulative_points, 1),
            }
        )

    return {
        "driver": f"{driver.forename} {driver.surname}",
        "season": season,
        "total_points": round(cumulative_points, 1),
        "rounds": progression,
    }


def compare_drivers(db: Session, d1: int, d2: int, season: Optional[int] = None):
    driver1 = db.query(Driver).filter(Driver.driver_id == d1).first()
    driver2 = db.query(Driver).filter(Driver.driver_id == d2).first()
    if not driver1 or not driver2:
        raise HTTPException(status_code=404, detail="One or both drivers not found")

    def get_stats(driver_id: int, season_filter: Optional[int] = None):
        query = db.query(Result).join(Race).filter(Result.driver_id == driver_id)
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
                sum(r.position for r in results if r.position) / max(sum(1 for r in results if r.position), 1),
                2,
            ),
        }

    d1_races = set(r.race_id for r in db.query(Result).filter(Result.driver_id == d1).all())
    d2_races = set(r.race_id for r in db.query(Result).filter(Result.driver_id == d2).all())
    common_races = d1_races & d2_races

    d1_ahead = 0
    d2_ahead = 0
    for race_id in common_races:
        r1 = db.query(Result).filter(Result.race_id == race_id, Result.driver_id == d1).first()
        r2 = db.query(Result).filter(Result.race_id == race_id, Result.driver_id == d2).first()
        if r1 and r2 and r1.position_order and r2.position_order:
            if r1.position_order < r2.position_order:
                d1_ahead += 1
            elif r2.position_order < r1.position_order:
                d2_ahead += 1

    return {
        "driver_1": {"name": f"{driver1.forename} {driver1.surname}", "stats": get_stats(d1, season)},
        "driver_2": {"name": f"{driver2.forename} {driver2.surname}", "stats": get_stats(d2, season)},
        "head_to_head": {
            "common_races": len(common_races),
            f"{driver1.surname}_ahead": d1_ahead,
            f"{driver2.surname}_ahead": d2_ahead,
        },
        "season_filter": season,
    }


def get_pit_stop_analysis(db: Session, race_id: int):
    race = db.query(Race).filter(Race.race_id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    pit_stops = db.query(PitStop).filter(PitStop.race_id == race_id).all()
    results = db.query(Result).filter(Result.race_id == race_id).all()

    if not pit_stops:
        raise HTTPException(status_code=404, detail="No pit stop data available for this race")

    driver_stops = {}
    for ps in pit_stops:
        driver_stops.setdefault(ps.driver_id, []).append(
            {"stop": ps.stop, "lap": ps.lap, "duration": ps.duration, "milliseconds": ps.milliseconds}
        )

    analysis = []
    for result in results:
        driver = db.query(Driver).filter(Driver.driver_id == result.driver_id).first()
        stops = driver_stops.get(result.driver_id, [])
        total_pit_time = sum(s["milliseconds"] or 0 for s in stops)

        analysis.append(
            {
                "driver": f"{driver.forename} {driver.surname}" if driver else "Unknown",
                "grid_position": result.grid,
                "final_position": result.position,
                "num_stops": len(stops),
                "total_pit_time_ms": total_pit_time,
                "stops_detail": stops,
            }
        )

    analysis.sort(key=lambda x: x["final_position"] or 999)

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
            "avg_finish_position": round(sum(v["avg_finish"]) / len(v["avg_finish"]), 1) if v["avg_finish"] else None,
        }
        for k, v in sorted(strategies.items())
    }

    return {
        "race": race.name,
        "season": race.year,
        "strategy_summary": strategy_summary,
        "driver_details": analysis,
    }


def get_circuit_history(db: Session, circuit_id: int):
    circuit = db.query(Race).filter(Race.circuit_id == circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="No races found for this circuit")

    circuit_info = (
        db.query(
            Race.circuit_id,
            func.count(Race.race_id).label("total_races"),
            func.min(Race.year).label("first_race"),
            func.max(Race.year).label("last_race"),
        )
        .filter(Race.circuit_id == circuit_id)
        .group_by(Race.circuit_id)
        .first()
    )

    race_ids = [r.race_id for r in db.query(Race).filter(Race.circuit_id == circuit_id).all()]
    winners = (
        db.query(Driver.forename, Driver.surname, func.count(Result.result_id).label("wins"))
        .join(Result, Result.driver_id == Driver.driver_id)
        .filter(Result.race_id.in_(race_ids), Result.position == 1)
        .group_by(Driver.driver_id, Driver.forename, Driver.surname)
        .order_by(desc("wins"))
        .limit(5)
        .all()
    )

    circuit_detail = db.query(CircuitModel).filter(CircuitModel.circuit_id == circuit_id).first()

    return {
        "circuit": {
            "name": circuit_detail.name if circuit_detail else "Unknown",
            "location": circuit_detail.location if circuit_detail else None,
            "country": circuit_detail.country if circuit_detail else None,
        },
        "statistics": {
            "total_races": circuit_info.total_races,
            "first_race_year": circuit_info.first_race,
            "last_race_year": circuit_info.last_race,
        },
        "most_successful_drivers": [{"driver": f"{w.forename} {w.surname}", "wins": w.wins} for w in winners],
    }
