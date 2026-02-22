from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Driver
from app.schemas import DriverCreate, DriverUpdate, DriverResponse
from app.utils.auth import get_current_user, require_admin
from sqlalchemy import func
from sqlalchemy import Integer

router = APIRouter(prefix="/api/v1/drivers", tags=["Drivers"])


@router.get("/", response_model=list[DriverResponse])
def get_drivers(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    nationality: Optional[str] = Query(None, description="Filter by nationality"),
    search: Optional[str] = Query(None, description="Search by name, surname, or driver_ref"),
    sort_by: Optional[str] = Query("newest", description="Sort by: 'newest', 'oldest', or 'popularity' (by total points)"),
    db: Session = Depends(get_db)
):
    """Get a paginated list of drivers with optional filters."""
    from app.models import Result

    query = db.query(Driver)

    if nationality:
        query = query.filter(Driver.nationality == nationality)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Driver.forename.ilike(search_pattern)) |
            (Driver.surname.ilike(search_pattern)) |
            (Driver.driver_ref.ilike(search_pattern)) |
            ((Driver.code.isnot(None)) & (Driver.code.ilike(search_pattern)))
        )

    if sort_by == "popularity":
        # 按总积分排序，积分高的车手更"出名"
        query = (
            query
            .outerjoin(Result, Driver.driver_id == Result.driver_id)
            .group_by(Driver.driver_id)
            .order_by(func.coalesce(func.sum(Result.points), 0).desc())
        )
    elif sort_by == "oldest":
        query = query.order_by(Driver.driver_id.asc())
    else:  # newest (default)
        query = query.order_by(Driver.driver_id.desc())

    offset = (page - 1) * per_page
    drivers = query.offset(offset).limit(per_page).all()
    return drivers


@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Get a single driver by ID."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def create_driver(
    driver_data: DriverCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new driver (requires authentication)."""
    driver = Driver(**driver_data.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@router.put("/{driver_id}", response_model=DriverResponse)
def update_driver(
    driver_id: int,
    driver_data: DriverUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update a driver (requires authentication)."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    update_data = driver_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(driver, field, value)

    db.commit()
    db.refresh(driver)
    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """Delete a driver (requires admin privileges)."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    db.delete(driver)
    db.commit()
