from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from app.database import get_db
from app.models import Circuit, Race, Result, Driver
from app.schemas import CircuitCreate, CircuitUpdate, CircuitResponse, CircuitListResponse, CircuitDetailResponse
from app.utils.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/circuits", tags=["Circuits"])


@router.get("/", response_model=list[CircuitListResponse],
    summary="List circuits with stats"
)
def get_circuits(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    country: Optional[str] = Query(None, description="Filter by country"),
    search: Optional[str] = Query(None, description="Search by circuit name or location"),
    sort_by: Optional[str] = Query(
        "name",
        description="Sort by: 'name' (alphabetical), 'country', 'most_races' (total races held), 'recent' (most recently used)"
    ),
    db: Session = Depends(get_db)
):
    """Get a paginated list of circuits with optional filters and sorting."""
    # Build a subquery with race stats (count + last year) per circuit
    race_stats_subq = (
        db.query(
            Race.circuit_id,
            func.count(Race.race_id).label("total_races"),
            func.max(Race.year).label("last_year"),
        )
        .group_by(Race.circuit_id)
        .subquery()
    )

    total_races_col = func.coalesce(race_stats_subq.c.total_races, 0)
    last_year_col = func.coalesce(race_stats_subq.c.last_year, 0)

    query = (
        db.query(Circuit, total_races_col.label("total_races"))
        .outerjoin(race_stats_subq, Circuit.circuit_id == race_stats_subq.c.circuit_id)
        .filter(Circuit.is_active == True)
    )

    # --- Filters ---
    if country:
        query = query.filter(Circuit.country.ilike(f"%{country}%"))
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Circuit.name.ilike(search_pattern)) |
            (Circuit.location.ilike(search_pattern)) |
            (Circuit.circuit_ref.ilike(search_pattern))
        )

    # --- Sorting ---
    if sort_by == "country":
        query = query.order_by(Circuit.country.asc(), Circuit.name.asc())
    elif sort_by == "most_races":
        query = query.order_by(total_races_col.desc())
    elif sort_by == "recent":
        query = query.order_by(last_year_col.desc())
    else:  # name (default)
        query = query.order_by(Circuit.name.asc())

    # --- Pagination ---
    offset = (page - 1) * per_page
    rows = query.offset(offset).limit(per_page).all()

    return [
        {**circuit.__dict__, "total_races": total_races}
        for circuit, total_races in rows
    ]


@router.get("/{circuit_id}", response_model=CircuitDetailResponse,
    summary="Get circuit detail with race history",
    responses={
        404: {"description": "Circuit not found",
              "content": {"application/json": {"example": {"detail": "Circuit not found"}}}},
    }
)
def get_circuit(circuit_id: int, db: Session = Depends(get_db)):
    """
    Get a single circuit by ID with recent race history.

    Returns circuit details plus the 5 most recent races held at this circuit,
    including the winner of each race.
    """
    circuit = db.query(Circuit).filter(Circuit.circuit_id == circuit_id, Circuit.is_active == True).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")

    # Fetch 5 most recent races at this circuit, with winner info
    recent_races_query = (
        db.query(Race, Result, Driver)
        .join(Result, Race.race_id == Result.race_id)
        .join(Driver, Result.driver_id == Driver.driver_id)
        .filter(Race.circuit_id == circuit_id, Result.position == 1)
        .order_by(Race.year.desc())
        .limit(5)
        .all()
    )

    recent_races = [
        {
            "race_id": race.race_id,
            "year": race.year,
            "round": race.round,
            "race_name": race.name,
            "date": str(race.date) if race.date else None,
            "winner": f"{driver.forename} {driver.surname}"
        }
        for race, result, driver in recent_races_query
    ]

    # Total races held
    total_races = db.query(func.count(Race.race_id)).filter(
        Race.circuit_id == circuit_id
    ).scalar()

    return {
        "circuit_id": circuit.circuit_id,
        "circuit_ref": circuit.circuit_ref,
        "name": circuit.name,
        "location": circuit.location,
        "country": circuit.country,
        "lat": circuit.lat,
        "lng": circuit.lng,
        "alt": circuit.alt,
        "url": circuit.url,
        "total_races_held": total_races,
        "recent_races": recent_races
    }


@router.post("/", response_model=CircuitResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a new circuit",
    responses={
        401: {"description": "Authentication required"},
        409: {"description": "Circuit ref already exists",
              "content": {"application/json": {"example": {"detail": "Circuit with ref 'silverstone' already exists"}}}},
    }
)
def create_circuit(
    circuit_data: CircuitCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new circuit (requires authentication)."""
    # Check for duplicate circuit_ref
    existing = db.query(Circuit).filter(Circuit.circuit_ref == circuit_data.circuit_ref).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Circuit with ref '{circuit_data.circuit_ref}' already exists"
        )

    circuit = Circuit(**circuit_data.model_dump())
    db.add(circuit)
    db.commit()
    db.refresh(circuit)
    return circuit


@router.put("/{circuit_id}", response_model=CircuitResponse,
    summary="Update a circuit",
    responses={
        400: {"description": "No fields to update"},
        401: {"description": "Authentication required"},
        404: {"description": "Circuit not found"},
    }
)
def update_circuit(
    circuit_id: int,
    circuit_data: CircuitUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update a circuit (requires authentication)."""
    circuit = db.query(Circuit).filter(Circuit.circuit_id == circuit_id, Circuit.is_active == True).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")

    update_data = circuit_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    for field, value in update_data.items():
        setattr(circuit, field, value)

    db.commit()
    db.refresh(circuit)
    return circuit


@router.delete("/{circuit_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a circuit",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Circuit not found"},
    }
)
def delete_circuit(
    circuit_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """Soft-delete a circuit (requires admin privileges). Historical data is preserved."""
    circuit = db.query(Circuit).filter(Circuit.circuit_id == circuit_id, Circuit.is_active == True).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")

    circuit.is_active = False
    db.commit()
