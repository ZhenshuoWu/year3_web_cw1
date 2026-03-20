from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Driver, Result
from app.schemas import DriverCreate, DriverUpdate, DriverResponse
from app.utils.auth import get_current_user, require_admin
from sqlalchemy import func
from sqlalchemy import Integer

router = APIRouter(prefix="/api/v1/drivers", tags=["Drivers"])


@router.get("/", response_model=list[DriverResponse],
    summary="List drivers"
)
def get_drivers(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    nationality: Optional[str] = Query(None, description="Filter by nationality"),
    search: Optional[str] = Query(None, description="Search by name, surname, or driver_ref"),
    sort_by: Optional[str] = Query(
        "newest",
        description="Sort by: 'newest', 'oldest', 'popularity' (all-time points), 'recent' (latest season points), 'wins' (total wins)"
    ),
    db: Session = Depends(get_db)
):
    """Get a paginated list of drivers with optional filters and smart sorting."""
    from sqlalchemy import func, desc
    from app.models import Result, Race

    query = db.query(Driver).filter(Driver.is_active == True)

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
        # All-time total points
        query = (
            query
            .outerjoin(Result, Driver.driver_id == Result.driver_id)
            .group_by(Driver.driver_id)
            .order_by(func.coalesce(func.sum(Result.points), 0).desc())
        )

    elif sort_by == "recent":
        # Latest season points — all drivers appear, historical drivers rank at 0
        latest_season = db.query(func.max(Race.year)).scalar()
        latest_pts_subq = (
            db.query(
                Result.driver_id,
                func.sum(Result.points).label("latest_points"),
            )
            .join(Race, Result.race_id == Race.race_id)
            .filter(Race.year == latest_season)
            .group_by(Result.driver_id)
            .subquery()
        )
        query = (
            query
            .outerjoin(latest_pts_subq, Driver.driver_id == latest_pts_subq.c.driver_id)
            .order_by(func.coalesce(latest_pts_subq.c.latest_points, 0).desc())
        )

    elif sort_by == "wins":
        # Total career wins
        win_count = func.sum(
            func.cast(Result.position == 1, Integer)
        )
        query = (
            query
            .outerjoin(Result, Driver.driver_id == Result.driver_id)
            .group_by(Driver.driver_id)
            .order_by(func.coalesce(win_count, 0).desc())
        )

    elif sort_by == "oldest":
        query = query.order_by(Driver.driver_id.asc())

    else:  # newest (default)
        query = query.order_by(Driver.driver_id.desc())

    offset = (page - 1) * per_page
    drivers = query.offset(offset).limit(per_page).all()
    return drivers


@router.get("/{driver_id}", response_model=DriverResponse,
    summary="Get driver by ID",
    responses={
        404: {"description": "Driver not found",
              "content": {"application/json": {"example": {"detail": "Driver not found"}}}},
    }
)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Get a single driver by ID."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id, Driver.is_active == True).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a new driver",
    responses={
        401: {"description": "Authentication required"},
        409: {"description": "Driver ref already exists",
              "content": {"application/json": {"example": {"detail": "Driver with ref 'hamilton' already exists"}}}},
    }
)
def create_driver(
    driver_data: DriverCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new driver (requires authentication)."""
    existing = db.query(Driver).filter(Driver.driver_ref == driver_data.driver_ref).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Driver with ref '{driver_data.driver_ref}' already exists"
        )
    driver = Driver(**driver_data.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@router.put("/{driver_id}", response_model=DriverResponse,
    summary="Update a driver",
    responses={
        400: {"description": "No fields to update",
              "content": {"application/json": {"example": {"detail": "No fields to update"}}}},
        401: {"description": "Authentication required"},
        404: {"description": "Driver not found"},
    }
)
def update_driver(
    driver_id: int,
    driver_data: DriverUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update a driver (requires authentication)."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id, Driver.is_active == True).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    update_data = driver_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    for field, value in update_data.items():
        setattr(driver, field, value)

    db.commit()
    db.refresh(driver)
    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a driver",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Driver not found"},
    }
)
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """Soft-delete a driver (requires admin privileges). Historical data is preserved."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id, Driver.is_active == True).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    driver.is_active = False
    db.commit()
