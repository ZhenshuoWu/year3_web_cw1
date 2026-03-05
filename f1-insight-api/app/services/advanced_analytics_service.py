from typing import Optional

from fastapi import HTTPException
from sqlalchemy import Float, and_, case, desc, func
from sqlalchemy.orm import Session

from app.models import Circuit, Constructor, Driver, PitStop, Qualifying, Race, Result


def get_win_probability(db: Session, driver_id: int, circuit_id: int):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    circuit = db.query(Circuit).filter(Circuit.circuit_id == circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")

    circuit_races = (
        db.query(Result, Race)
        .join(Race, Result.race_id == Race.race_id)
        .filter(Result.driver_id == driver_id, Race.circuit_id == circuit_id)
        .all()
    )
    circuit_starts = len(circuit_races)
    circuit_wins = sum(1 for r, _ in circuit_races if r.position == 1)
    circuit_podiums = sum(1 for r, _ in circuit_races if r.position and r.position <= 3)
    circuit_avg_finish = (
        sum(r.position for r, _ in circuit_races if r.position) / max(sum(1 for r, _ in circuit_races if r.position), 1)
    )
    circuit_win_rate = (circuit_wins / circuit_starts * 100) if circuit_starts > 0 else 0

    recent_results = (
        db.query(Result, Race)
        .join(Race, Result.race_id == Race.race_id)
        .filter(Result.driver_id == driver_id)
        .order_by(Race.date.desc())
        .limit(5)
        .all()
    )
    recent_wins = sum(1 for r, _ in recent_results if r.position == 1)
    recent_podiums = sum(1 for r, _ in recent_results if r.position and r.position <= 3)
    recent_avg_finish = (
        sum(r.position for r, _ in recent_results if r.position) / max(sum(1 for r, _ in recent_results if r.position), 1)
    )
    recent_form_score = max(0, min(100, (20 - recent_avg_finish) / 19 * 100)) if recent_results else 0

    grid_results = db.query(Result).filter(Result.driver_id == driver_id, Result.grid.isnot(None), Result.grid > 0).all()
    front_row_starts = sum(1 for r in grid_results if r.grid <= 2)
    front_row_wins = sum(1 for r in grid_results if r.grid <= 2 and r.position == 1)
    grid_conversion = (front_row_wins / front_row_starts * 100) if front_row_starts > 0 else 0

    all_results = db.query(Result).filter(Result.driver_id == driver_id).all()
    total_races = len(all_results)
    total_wins = sum(1 for r in all_results if r.position == 1)
    career_win_rate = (total_wins / total_races * 100) if total_races > 0 else 0

    probability = round(
        min(circuit_win_rate * 0.35 + recent_form_score * 0.30 + grid_conversion * 0.20 + career_win_rate * 0.15, 99.9), 1
    )

    return {
        "driver": f"{driver.forename} {driver.surname}",
        "circuit": circuit.name,
        "win_probability": f"{probability}%",
        "factors": {
            "circuit_history": {
                "weight": "35%",
                "score": round(circuit_win_rate, 1),
                "detail": {
                    "races_at_circuit": circuit_starts,
                    "wins_at_circuit": circuit_wins,
                    "podiums_at_circuit": circuit_podiums,
                    "avg_finish_at_circuit": round(circuit_avg_finish, 1) if circuit_starts > 0 else None,
                },
            },
            "recent_form": {
                "weight": "30%",
                "score": round(recent_form_score, 1),
                "detail": {
                    "last_5_races_avg_finish": round(recent_avg_finish, 1) if recent_results else None,
                    "last_5_wins": recent_wins,
                    "last_5_podiums": recent_podiums,
                },
            },
            "grid_conversion": {
                "weight": "20%",
                "score": round(grid_conversion, 1),
                "detail": {"front_row_starts": front_row_starts, "front_row_wins": front_row_wins},
            },
            "career_baseline": {
                "weight": "15%",
                "score": round(career_win_rate, 1),
                "detail": {"total_races": total_races, "total_wins": total_wins},
            },
        },
        "note": "Probability is estimated from historical data and weighted across four factors. It does not account for current car performance or regulation changes.",
    }


def get_performance_summary(db: Session, driver_id: int, season: Optional[int] = None):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    results_query = db.query(Result, Race).join(Race, Result.race_id == Race.race_id).filter(Result.driver_id == driver_id)
    if season:
        results_query = results_query.filter(Race.year == season)

    results = results_query.all()
    if not results:
        raise HTTPException(status_code=404, detail="No data found for this driver" + (f" in {season}" if season else ""))

    total_races = len(results)

    qualifying_data = db.query(Qualifying, Race).join(Race, Qualifying.race_id == Race.race_id).filter(Qualifying.driver_id == driver_id)
    if season:
        qualifying_data = qualifying_data.filter(Race.year == season)
    qualifying_data = qualifying_data.all()

    if qualifying_data:
        avg_quali_pos = sum(q.position for q, _ in qualifying_data if q.position) / max(
            sum(1 for q, _ in qualifying_data if q.position), 1
        )
        pole_positions = sum(1 for q, _ in qualifying_data if q.position == 1)
        top3_quali = sum(1 for q, _ in qualifying_data if q.position and q.position <= 3)
        quali_score = max(0, min(100, (20 - avg_quali_pos) / 19 * 100))
    else:
        avg_quali_pos = None
        pole_positions = 0
        top3_quali = 0
        quali_score = 50

    finishes = [(r, race) for r, race in results if r.position is not None]
    avg_finish = sum(r.position for r, _ in finishes) / max(len(finishes), 1)
    wins = sum(1 for r, _ in results if r.position == 1)
    podiums = sum(1 for r, _ in results if r.position and r.position <= 3)
    points_per_race = sum(r.points or 0 for r, _ in results) / max(total_races, 1)
    race_pace_score = max(0, min(100, (20 - avg_finish) / 19 * 100))

    points_finishes = sum(1 for r, _ in results if r.points and r.points > 0)
    dnfs = sum(1 for r, _ in results if r.position is None)
    finish_rate = (total_races - dnfs) / max(total_races, 1) * 100
    points_finish_rate = points_finishes / max(total_races, 1) * 100
    consistency_score = finish_rate * 0.4 + points_finish_rate * 0.6

    grid_vs_finish = [(r.grid - r.position) for r, _ in results if r.grid and r.position and r.grid > 0]
    avg_positions_gained = sum(grid_vs_finish) / max(len(grid_vs_finish), 1) if grid_vs_finish else 0
    overtaking_score = max(0, min(100, (avg_positions_gained + 5) / 10 * 100))

    pit_query = db.query(PitStop).join(Race, PitStop.race_id == Race.race_id).filter(PitStop.driver_id == driver_id)
    if season:
        pit_query = pit_query.filter(Race.year == season)
    pit_stops = pit_query.all()

    if pit_stops:
        pit_times = [p.milliseconds for p in pit_stops if p.milliseconds and p.milliseconds > 0]
        avg_pit_time = sum(pit_times) / max(len(pit_times), 1) if pit_times else None
        pit_score = max(0, min(100, (40000 - (avg_pit_time or 30000)) / 20000 * 100))
    else:
        avg_pit_time = None
        pit_score = 50

    overall = quali_score * 0.25 + race_pace_score * 0.30 + consistency_score * 0.20 + overtaking_score * 0.15 + pit_score * 0.10

    return {
        "driver": f"{driver.forename} {driver.surname}",
        "season": season or "all-time",
        "overall_rating": round(overall, 1),
        "total_races": total_races,
        "dimensions": {
            "qualifying_pace": {
                "score": round(quali_score, 1),
                "weight": "25%",
                "detail": {
                    "avg_qualifying_position": round(avg_quali_pos, 1) if avg_quali_pos else None,
                    "pole_positions": pole_positions,
                    "top_3_qualifying": top3_quali,
                },
            },
            "race_pace": {
                "score": round(race_pace_score, 1),
                "weight": "30%",
                "detail": {
                    "avg_finish_position": round(avg_finish, 1),
                    "wins": wins,
                    "podiums": podiums,
                    "points_per_race": round(points_per_race, 1),
                },
            },
            "consistency": {
                "score": round(consistency_score, 1),
                "weight": "20%",
                "detail": {
                    "finish_rate": f"{round(finish_rate, 1)}%",
                    "points_finish_rate": f"{round(points_finish_rate, 1)}%",
                    "dnfs": dnfs,
                },
            },
            "overtaking": {
                "score": round(overtaking_score, 1),
                "weight": "15%",
                "detail": {
                    "avg_positions_gained": round(avg_positions_gained, 1),
                    "races_analysed": len(grid_vs_finish),
                },
            },
            "pit_stop_efficiency": {
                "score": round(pit_score, 1),
                "weight": "10%",
                "detail": {"avg_pit_time_ms": round(avg_pit_time) if avg_pit_time else None, "total_pit_stops": len(pit_stops)},
            },
        },
    }


def get_teammate_battle(db: Session, driver_id: int, season: int):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    driver_results = (
        db.query(Result, Race).join(Race, Result.race_id == Race.race_id).filter(Result.driver_id == driver_id, Race.year == season).all()
    )
    if not driver_results:
        raise HTTPException(status_code=404, detail=f"No data for this driver in {season}")

    constructor_ids = set(r.constructor_id for r, _ in driver_results)
    battles = []

    for cid in constructor_ids:
        constructor = db.query(Constructor).filter(Constructor.constructor_id == cid).first()
        teammate_ids = (
            db.query(Result.driver_id)
            .join(Race, Result.race_id == Race.race_id)
            .filter(Result.constructor_id == cid, Race.year == season, Result.driver_id != driver_id)
            .distinct()
            .all()
        )

        for (tid,) in teammate_ids:
            teammate = db.query(Driver).filter(Driver.driver_id == tid).first()
            if not teammate:
                continue

            driver_race_ids = set(r.race_id for r, _ in driver_results if r.constructor_id == cid)
            teammate_results = (
                db.query(Result)
                .join(Race, Result.race_id == Race.race_id)
                .filter(Result.driver_id == tid, Result.constructor_id == cid, Race.year == season)
                .all()
            )
            teammate_race_ids = set(r.race_id for r in teammate_results)
            common_races = driver_race_ids & teammate_race_ids

            quali_driver_ahead = 0
            quali_teammate_ahead = 0
            for rid in common_races:
                dq = db.query(Qualifying).filter(Qualifying.race_id == rid, Qualifying.driver_id == driver_id).first()
                tq = db.query(Qualifying).filter(Qualifying.race_id == rid, Qualifying.driver_id == tid).first()
                if dq and tq and dq.position and tq.position:
                    if dq.position < tq.position:
                        quali_driver_ahead += 1
                    elif tq.position < dq.position:
                        quali_teammate_ahead += 1

            race_driver_ahead = 0
            race_teammate_ahead = 0
            driver_total_points = 0
            teammate_total_points = 0
            for rid in common_races:
                dr = (
                    db.query(Result)
                    .filter(Result.race_id == rid, Result.driver_id == driver_id, Result.constructor_id == cid)
                    .first()
                )
                tr = db.query(Result).filter(Result.race_id == rid, Result.driver_id == tid, Result.constructor_id == cid).first()
                if dr and tr:
                    driver_total_points += dr.points or 0
                    teammate_total_points += tr.points or 0
                    if dr.position_order and tr.position_order:
                        if dr.position_order < tr.position_order:
                            race_driver_ahead += 1
                        elif tr.position_order < dr.position_order:
                            race_teammate_ahead += 1

            battles.append(
                {
                    "constructor": constructor.name if constructor else "Unknown",
                    "teammate": f"{teammate.forename} {teammate.surname}",
                    "common_races": len(common_races),
                    "qualifying": {
                        f"{driver.surname}": quali_driver_ahead,
                        f"{teammate.surname}": quali_teammate_ahead,
                        "winner": (
                            driver.surname
                            if quali_driver_ahead > quali_teammate_ahead
                            else teammate.surname if quali_teammate_ahead > quali_driver_ahead else "Tied"
                        ),
                    },
                    "race": {
                        f"{driver.surname}": race_driver_ahead,
                        f"{teammate.surname}": race_teammate_ahead,
                        "winner": (
                            driver.surname
                            if race_driver_ahead > race_teammate_ahead
                            else teammate.surname if race_teammate_ahead > race_driver_ahead else "Tied"
                        ),
                    },
                    "points": {
                        f"{driver.surname}": round(driver_total_points, 1),
                        f"{teammate.surname}": round(teammate_total_points, 1),
                        "winner": (
                            driver.surname
                            if driver_total_points > teammate_total_points
                            else teammate.surname if teammate_total_points > driver_total_points else "Tied"
                        ),
                    },
                }
            )

    return {"driver": f"{driver.forename} {driver.surname}", "season": season, "battles": battles}


def get_leaderboard(db: Session, season: Optional[int], metric: str, limit: int):
    query = (
        db.query(
            Driver.driver_id,
            Driver.forename,
            Driver.surname,
            Driver.nationality,
            func.count(Result.result_id).label("races"),
            func.coalesce(func.sum(Result.points), 0).label("total_points"),
            func.sum(case((Result.position == 1, 1), else_=0)).label("wins"),
            func.sum(case((and_(Result.position.isnot(None), Result.position <= 3), 1), else_=0)).label("podiums"),
        )
        .join(Result, Driver.driver_id == Result.driver_id)
        .join(Race, Result.race_id == Race.race_id)
    )

    if season:
        query = query.filter(Race.year == season)

    query = query.group_by(Driver.driver_id, Driver.forename, Driver.surname, Driver.nationality)

    if metric == "wins":
        query = query.order_by(desc("wins"), desc("total_points"))
    elif metric == "podiums":
        query = query.order_by(desc("podiums"), desc("total_points"))
    elif metric == "win_rate":
        min_races = 5 if season else 20
        query = query.having(func.count(Result.result_id) >= min_races)
        win_rate_expr = (func.sum(case((Result.position == 1, 1), else_=0)).cast(Float) / func.count(Result.result_id)).desc()
        query = query.order_by(win_rate_expr)
    else:
        query = query.order_by(desc("total_points"))

    results = query.limit(limit).all()

    leaderboard = []
    for i, row in enumerate(results, 1):
        races = row.races
        wins = row.wins
        leaderboard.append(
            {
                "rank": i,
                "driver": f"{row.forename} {row.surname}",
                "nationality": row.nationality,
                "races": races,
                "wins": wins,
                "podiums": row.podiums,
                "total_points": round(float(row.total_points), 1),
                "win_rate": f"{round(wins / races * 100, 1)}%" if races > 0 else "0%",
            }
        )

    return {"season": season or "all-time", "metric": metric, "total_drivers": len(leaderboard), "leaderboard": leaderboard}
