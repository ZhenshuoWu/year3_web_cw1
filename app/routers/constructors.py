from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import Optional
from app.database import get_db
from app.models import Constructor, Result, Race, Driver
from app.schemas import ConstructorCreate, ConstructorUpdate, ConstructorResponse, ConstructorListResponse, ConstructorDetailResponse
from app.utils.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/constructors", tags=["Constructors"])


@router.get("/", response_model=list[ConstructorListResponse],
    summary="List constructors with stats"
)
def get_constructors(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    nationality: Optional[str] = Query(None, description="Filter by nationality"),
    search: Optional[str] = Query(None, description="Search by constructor name or ref"),
    sort_by: Optional[str] = Query(
        "name",
        description="Sort by: 'name' (alphabetical), 'nationality', 'total_points' (all-time points), 'wins' (total wins), 'recent' (most recently active)"
    ),
    db: Session = Depends(get_db)
):
    """Get a paginated list of constructors with optional filters and sorting."""
    # Build a single stats subquery: all-time points, wins, and last active year per constructor
    stats_subq = (
        db.query(
            Result.constructor_id,
            func.coalesce(func.sum(Result.points), 0).label("total_points"),
            func.sum(case((Result.position == 1, 1), else_=0)).label("wins"),
            func.max(Race.year).label("last_year"),
        )
        .join(Race, Result.race_id == Race.race_id)
        .group_by(Result.constructor_id)
        .subquery()
    )

    total_points_col = func.coalesce(stats_subq.c.total_points, 0)
    wins_col = func.coalesce(stats_subq.c.wins, 0)
    last_year_col = func.coalesce(stats_subq.c.last_year, 0)

    query = (
        db.query(
            Constructor,
            total_points_col.label("total_points"),
            wins_col.label("wins"),
        )
        .outerjoin(stats_subq, Constructor.constructor_id == stats_subq.c.constructor_id)
        .filter(Constructor.is_active == True)
    )

    # --- Filters ---
    if nationality:
        query = query.filter(Constructor.nationality.ilike(f"%{nationality}%"))
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Constructor.name.ilike(search_pattern)) |
            (Constructor.constructor_ref.ilike(search_pattern))
        )

    # --- Sorting ---
    if sort_by == "nationality":
        query = query.order_by(Constructor.nationality.asc(), Constructor.name.asc())
    elif sort_by == "total_points":
        query = query.order_by(total_points_col.desc())
    elif sort_by == "wins":
        query = query.order_by(wins_col.desc())
    elif sort_by == "recent":
        query = query.order_by(last_year_col.desc(), Constructor.name.asc())
    else:  # name (default)
        query = query.order_by(Constructor.name.asc())

    # --- Pagination ---
    offset = (page - 1) * per_page
    rows = query.offset(offset).limit(per_page).all()

    return [
        {**constructor.__dict__, "total_points": total_points, "wins": wins}
        for constructor, total_points, wins in rows
    ]


@router.get("/{constructor_id}", response_model=ConstructorDetailResponse,
    summary="Get constructor detail with career summary",
    responses={
        404: {"description": "Constructor not found",
              "content": {"application/json": {"example": {"detail": "Constructor not found"}}}},
    }
)
def get_constructor(constructor_id: int, db: Session = Depends(get_db)):
    """
    Get a single constructor by ID with career summary and notable drivers.

    Returns constructor details plus all-time stats (total races, wins, points)
    and the top 5 highest-scoring drivers who raced for this team.
    """
    constructor = db.query(Constructor).filter(
        Constructor.constructor_id == constructor_id,
        Constructor.is_active == True
    ).first()
    if not constructor:
        raise HTTPException(status_code=404, detail="Constructor not found")

    # --- Career summary via aggregation ---
    stats = (
        db.query(
            func.count(Result.result_id).label("total_entries"),
            func.coalesce(func.sum(Result.points), 0).label("total_points"),
            func.sum(case((Result.position == 1, 1), else_=0)).label("wins"),
            func.sum(case((Result.position <= 3, 1), else_=0)).label("podiums"),
        )
        .filter(Result.constructor_id == constructor_id)
        .first()
    )

    # --- Season range ---
    season_range = (
        db.query(func.min(Race.year), func.max(Race.year))
        .join(Result, Race.race_id == Result.race_id)
        .filter(Result.constructor_id == constructor_id)
        .first()
    )

    # --- Top 5 drivers by points scored for this constructor ---
    top_drivers = (
        db.query(
            Driver.forename,
            Driver.surname,
            func.count(Result.result_id).label("races"),
            func.coalesce(func.sum(Result.points), 0).label("points"),
            func.sum(case((Result.position == 1, 1), else_=0)).label("wins"),
        )
        .join(Result, Driver.driver_id == Result.driver_id)
        .filter(Result.constructor_id == constructor_id)
        .group_by(Driver.driver_id, Driver.forename, Driver.surname)
        .order_by(func.coalesce(func.sum(Result.points), 0).desc())
        .limit(5)
        .all()
    )

    return {
        "constructor_id": constructor.constructor_id,
        "constructor_ref": constructor.constructor_ref,
        "name": constructor.name,
        "nationality": constructor.nationality,
        "url": constructor.url,
        "career_summary": {
            "total_entries": stats.total_entries if stats else 0,
            "total_points": round(float(stats.total_points), 1) if stats else 0,
            "wins": stats.wins if stats else 0,
            "podiums": stats.podiums if stats else 0,
            "first_season": season_range[0] if season_range else None,
            "last_season": season_range[1] if season_range else None,
        },
        "top_drivers": [
            {
                "driver": f"{d.forename} {d.surname}",
                "races_for_team": d.races,
                "points_for_team": round(float(d.points), 1),
                "wins_for_team": d.wins,
            }
            for d in top_drivers
        ]
    }


@router.post("/", response_model=ConstructorResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a new constructor",
    responses={
        401: {"description": "Authentication required"},
        409: {"description": "Constructor ref already exists",
              "content": {"application/json": {"example": {"detail": "Constructor with ref 'mercedes' already exists"}}}},
    }
)
def create_constructor(
    constructor_data: ConstructorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new constructor (requires authentication)."""
    existing = db.query(Constructor).filter(
        Constructor.constructor_ref == constructor_data.constructor_ref
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Constructor with ref '{constructor_data.constructor_ref}' already exists"
        )

    constructor = Constructor(**constructor_data.model_dump())
    db.add(constructor)
    db.commit()
    db.refresh(constructor)
    return constructor


@router.put("/{constructor_id}", response_model=ConstructorResponse,
    summary="Update a constructor",
    responses={
        400: {"description": "No fields to update"},
        401: {"description": "Authentication required"},
        404: {"description": "Constructor not found"},
    }
)
def update_constructor(
    constructor_id: int,
    constructor_data: ConstructorUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update a constructor (requires authentication)."""
    constructor = db.query(Constructor).filter(
        Constructor.constructor_id == constructor_id,
        Constructor.is_active == True
    ).first()
    if not constructor:
        raise HTTPException(status_code=404, detail="Constructor not found")

    update_data = constructor_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    for field, value in update_data.items():
        setattr(constructor, field, value)

    db.commit()
    db.refresh(constructor)
    return constructor


@router.delete("/{constructor_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a constructor",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Constructor not found"},
    }
)
def delete_constructor(
    constructor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """Soft-delete a constructor (requires admin privileges). Historical data is preserved."""
    constructor = db.query(Constructor).filter(
        Constructor.constructor_id == constructor_id,
        Constructor.is_active == True
    ).first()
    if not constructor:
        raise HTTPException(status_code=404, detail="Constructor not found")

    constructor.is_active = False
    db.commit()
