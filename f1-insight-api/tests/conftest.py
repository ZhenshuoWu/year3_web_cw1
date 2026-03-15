import pytest
from datetime import date
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import (
    Season, Circuit, Driver, Constructor, Status,
    Race, Result, Qualifying, PitStop, User,
)
from app.utils.auth import get_password_hash, create_access_token


# ---------------------------------------------------------------------------
# SQLite in-memory engine — StaticPool shares a single connection so tables
# created by create_all are visible to all sessions in the same test.
# ---------------------------------------------------------------------------
SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable WAL-like behaviour: SQLite needs PRAGMA foreign_keys per connection
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def db_session():
    """Create tables before each test, drop them after."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_get_db(db_session):
    """Redirect FastAPI's get_db dependency to the test session."""
    def _override():
        try:
            yield db_session
        finally:
            pass  # session lifecycle managed by db_session fixture

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Auth helper fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def test_user(db_session):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_user(db_session):
    user = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_headers(test_user):
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(admin_user):
    token = create_access_token(data={"sub": admin_user.username})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Seed-data fixtures (for analytics tests that need a populated DB)
# ---------------------------------------------------------------------------
@pytest.fixture()
def seed_data(db_session):
    """Insert a minimal but realistic F1 dataset for integration tests."""
    # Season
    s2023 = Season(year=2023, url="http://example.com/2023")
    s2024 = Season(year=2024, url="http://example.com/2024")
    db_session.add_all([s2023, s2024])
    db_session.flush()

    # Circuit
    monza = Circuit(
        circuit_id=1, circuit_ref="monza", name="Monza",
        location="Monza", country="Italy", lat=45.6, lng=9.3, alt=162,
    )
    silverstone = Circuit(
        circuit_id=2, circuit_ref="silverstone", name="Silverstone",
        location="Silverstone", country="UK", lat=52.0, lng=-1.0, alt=153,
    )
    db_session.add_all([monza, silverstone])
    db_session.flush()

    # Drivers
    hamilton = Driver(
        driver_id=1, driver_ref="hamilton", number=44, code="HAM",
        forename="Lewis", surname="Hamilton", dob=date(1985, 1, 7),
        nationality="British",
    )
    verstappen = Driver(
        driver_id=2, driver_ref="max_verstappen", number=1, code="VER",
        forename="Max", surname="Verstappen", dob=date(1997, 9, 30),
        nationality="Dutch",
    )
    norris = Driver(
        driver_id=3, driver_ref="norris", number=4, code="NOR",
        forename="Lando", surname="Norris", dob=date(1999, 11, 13),
        nationality="British",
    )
    db_session.add_all([hamilton, verstappen, norris])
    db_session.flush()

    # Constructors
    mercedes = Constructor(
        constructor_id=1, constructor_ref="mercedes",
        name="Mercedes", nationality="German",
    )
    red_bull = Constructor(
        constructor_id=2, constructor_ref="red_bull",
        name="Red Bull", nationality="Austrian",
    )
    mclaren = Constructor(
        constructor_id=3, constructor_ref="mclaren",
        name="McLaren", nationality="British",
    )
    db_session.add_all([mercedes, red_bull, mclaren])
    db_session.flush()

    # Status
    finished = Status(status_id=1, status="Finished")
    retired = Status(status_id=2, status="Retired")
    db_session.add_all([finished, retired])
    db_session.flush()

    # Races
    race1 = Race(
        race_id=1, year=2023, round=1, circuit_id=1,
        name="Italian Grand Prix", date=date(2023, 9, 3),
    )
    race2 = Race(
        race_id=2, year=2023, round=2, circuit_id=2,
        name="British Grand Prix", date=date(2023, 7, 9),
    )
    race3 = Race(
        race_id=3, year=2024, round=1, circuit_id=1,
        name="Italian Grand Prix 2024", date=date(2024, 9, 1),
    )
    db_session.add_all([race1, race2, race3])
    db_session.flush()

    # Results — Hamilton wins race1, Verstappen wins race2 & race3
    results = [
        # Race 1 (Monza 2023)
        Result(result_id=1, race_id=1, driver_id=1, constructor_id=1,
               grid=1, position=1, position_text="1", position_order=1,
               points=25, laps=53, status_id=1),
        Result(result_id=2, race_id=1, driver_id=2, constructor_id=2,
               grid=2, position=2, position_text="2", position_order=2,
               points=18, laps=53, status_id=1),
        Result(result_id=3, race_id=1, driver_id=3, constructor_id=3,
               grid=3, position=3, position_text="3", position_order=3,
               points=15, laps=53, status_id=1),
        # Race 2 (Silverstone 2023)
        Result(result_id=4, race_id=2, driver_id=2, constructor_id=2,
               grid=1, position=1, position_text="1", position_order=1,
               points=25, laps=52, status_id=1),
        Result(result_id=5, race_id=2, driver_id=1, constructor_id=1,
               grid=3, position=2, position_text="2", position_order=2,
               points=18, laps=52, status_id=1),
        Result(result_id=6, race_id=2, driver_id=3, constructor_id=3,
               grid=5, position=None, position_text="R", position_order=20,
               points=0, laps=30, status_id=2),
        # Race 3 (Monza 2024)
        Result(result_id=7, race_id=3, driver_id=2, constructor_id=2,
               grid=1, position=1, position_text="1", position_order=1,
               points=25, laps=53, status_id=1),
        Result(result_id=8, race_id=3, driver_id=1, constructor_id=1,
               grid=2, position=3, position_text="3", position_order=3,
               points=15, laps=53, status_id=1),
    ]
    db_session.add_all(results)
    db_session.flush()

    # Qualifying
    quals = [
        Qualifying(qualify_id=1, race_id=1, driver_id=1, constructor_id=1, position=1),
        Qualifying(qualify_id=2, race_id=1, driver_id=2, constructor_id=2, position=2),
        Qualifying(qualify_id=3, race_id=1, driver_id=3, constructor_id=3, position=3),
        Qualifying(qualify_id=4, race_id=2, driver_id=2, constructor_id=2, position=1),
        Qualifying(qualify_id=5, race_id=2, driver_id=1, constructor_id=1, position=3),
    ]
    db_session.add_all(quals)
    db_session.flush()

    # Pit stops
    pits = [
        PitStop(race_id=1, driver_id=1, stop=1, lap=20, duration="23.5", milliseconds=23500),
        PitStop(race_id=1, driver_id=1, stop=2, lap=40, duration="24.0", milliseconds=24000),
        PitStop(race_id=1, driver_id=2, stop=1, lap=22, duration="22.8", milliseconds=22800),
        PitStop(race_id=2, driver_id=2, stop=1, lap=18, duration="21.5", milliseconds=21500),
        PitStop(race_id=2, driver_id=1, stop=1, lap=19, duration="25.0", milliseconds=25000),
    ]
    db_session.add_all(pits)
    db_session.commit()

    return {
        "drivers": {"hamilton": hamilton, "verstappen": verstappen, "norris": norris},
        "constructors": {"mercedes": mercedes, "red_bull": red_bull, "mclaren": mclaren},
        "circuits": {"monza": monza, "silverstone": silverstone},
        "races": {"race1": race1, "race2": race2, "race3": race3},
    }
