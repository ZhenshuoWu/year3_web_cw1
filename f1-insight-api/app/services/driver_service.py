from typing import Optional

from fastapi import HTTPException
from sqlalchemy import Integer, func
from sqlalchemy.orm import Session

from app.models import Driver, Race, Result
from app.schemas import DriverCreate, DriverUpdate


def list_drivers(
    db: Session,
    page: int,
    per_page: int,
    nationality: Optional[str],
    search: Optional[str],
    sort_by: Optional[str],
):
    query = db.query(Driver)

    if nationality:
        query = query.filter(Driver.nationality == nationality)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Driver.forename.ilike(search_pattern))
            | (Driver.surname.ilike(search_pattern))
            | (Driver.driver_ref.ilike(search_pattern))
            | ((Driver.code.isnot(None)) & (Driver.code.ilike(search_pattern)))
        )

    if sort_by == "popularity":
        query = (
            query.outerjoin(Result, Driver.driver_id == Result.driver_id)
            .group_by(Driver.driver_id)
            .order_by(func.coalesce(func.sum(Result.points), 0).desc())
        )
    elif sort_by == "recent":
        latest_season = db.query(func.max(Race.year)).scalar()
        query = (
            query.outerjoin(Result, Driver.driver_id == Result.driver_id)
            .outerjoin(Race, Result.race_id == Race.race_id)
            .filter((Race.year == latest_season) | (Race.year.is_(None)))
            .group_by(Driver.driver_id)
            .order_by(func.coalesce(func.sum(Result.points), 0).desc())
        )
    elif sort_by == "wins":
        win_count = func.sum(func.cast(Result.position == 1, Integer))
        query = (
            query.outerjoin(Result, Driver.driver_id == Result.driver_id)
            .group_by(Driver.driver_id)
            .order_by(func.coalesce(win_count, 0).desc())
        )
    elif sort_by == "oldest":
        query = query.order_by(Driver.driver_id.asc())
    else:
        query = query.order_by(Driver.driver_id.desc())

    offset = (page - 1) * per_page
    return query.offset(offset).limit(per_page).all()


def get_driver_by_id(db: Session, driver_id: int) -> Driver:
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


def create_driver(db: Session, driver_data: DriverCreate) -> Driver:
    driver = Driver(**driver_data.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


def update_driver(db: Session, driver_id: int, driver_data: DriverUpdate) -> Driver:
    driver = get_driver_by_id(db, driver_id)
    for field, value in driver_data.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)
    db.commit()
    db.refresh(driver)
    return driver


def delete_driver(db: Session, driver_id: int) -> None:
    driver = get_driver_by_id(db, driver_id)
    db.delete(driver)
    db.commit()
