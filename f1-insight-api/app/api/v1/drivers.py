from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas import DriverCreate, DriverUpdate, DriverResponse
from app.services.driver_service import (
    create_driver as create_driver_service,
    delete_driver as delete_driver_service,
    get_driver_by_id,
    list_drivers,
    update_driver as update_driver_service,
)
from app.utils.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/drivers", tags=["Drivers"])


@router.get("/", response_model=list[DriverResponse])
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
    return list_drivers(
        db=db,
        page=page,
        per_page=per_page,
        nationality=nationality,
        search=search,
        sort_by=sort_by,
    )


@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Get a single driver by ID."""
    return get_driver_by_id(db, driver_id)


@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def create_driver(
    driver_data: DriverCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new driver (requires authentication)."""
    return create_driver_service(db, driver_data)


@router.put("/{driver_id}", response_model=DriverResponse)
def update_driver(
    driver_id: int,
    driver_data: DriverUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update a driver (requires authentication)."""
    return update_driver_service(db, driver_id, driver_data)


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """Delete a driver (requires admin privileges)."""
    delete_driver_service(db, driver_id)
