from sqlalchemy import Column, Integer, String, Float, Date, Time, ForeignKey, Text, Index, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.database import Base


class Season(Base):
    __tablename__ = "seasons"

    year = Column(Integer, primary_key=True)
    url = Column(String(500))

    races = relationship("Race", back_populates="season")


class Circuit(Base):
    __tablename__ = "circuits"

    circuit_id = Column(Integer, primary_key=True)
    circuit_ref = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    country = Column(String(255))
    lat = Column(Float)
    lng = Column(Float)
    alt = Column(Float)
    url = Column(String(500))
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")

    races = relationship("Race", back_populates="circuit")


class Driver(Base):
    __tablename__ = "drivers"

    driver_id = Column(Integer, primary_key=True)
    driver_ref = Column(String(255), nullable=False)
    number = Column(Integer, nullable=True)
    code = Column(String(10), nullable=True)
    forename = Column(String(255), nullable=False)
    surname = Column(String(255), nullable=False)
    dob = Column(Date, nullable=True)
    nationality = Column(String(255))
    url = Column(String(500))
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")

    results = relationship("Result", back_populates="driver")
    qualifying_results = relationship("Qualifying", back_populates="driver")
    pit_stops = relationship("PitStop", back_populates="driver")
    lap_times = relationship("LapTime", back_populates="driver")


class Constructor(Base):
    __tablename__ = "constructors"

    constructor_id = Column(Integer, primary_key=True)
    constructor_ref = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    nationality = Column(String(255))
    url = Column(String(500))
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")

    results = relationship("Result", back_populates="constructor")
    qualifying_results = relationship("Qualifying", back_populates="constructor")


class Status(Base):
    __tablename__ = "status"

    status_id = Column(Integer, primary_key=True)
    status = Column(String(255), nullable=False)

    results = relationship("Result", back_populates="status_info")


class Race(Base):
    __tablename__ = "races"

    race_id = Column(Integer, primary_key=True)
    year = Column(Integer, ForeignKey("seasons.year"), nullable=False, index=True)
    round = Column(Integer, nullable=False)
    circuit_id = Column(Integer, ForeignKey("circuits.circuit_id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    date = Column(Date)
    time = Column(String(50), nullable=True)
    url = Column(String(500))
    fp1_date = Column(Date, nullable=True)
    fp1_time = Column(String(50), nullable=True)
    fp2_date = Column(Date, nullable=True)
    fp2_time = Column(String(50), nullable=True)
    fp3_date = Column(Date, nullable=True)
    fp3_time = Column(String(50), nullable=True)
    quali_date = Column(Date, nullable=True)
    quali_time = Column(String(50), nullable=True)
    sprint_date = Column(Date, nullable=True)
    sprint_time = Column(String(50), nullable=True)

    season = relationship("Season", back_populates="races")
    circuit = relationship("Circuit", back_populates="races")
    results = relationship("Result", back_populates="race")
    qualifying_results = relationship("Qualifying", back_populates="race")
    pit_stops = relationship("PitStop", back_populates="race")
    lap_times = relationship("LapTime", back_populates="race")


class Result(Base):
    __tablename__ = "results"

    result_id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey("races.race_id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"), nullable=False, index=True)
    constructor_id = Column(Integer, ForeignKey("constructors.constructor_id"), nullable=False, index=True)
    number = Column(Integer, nullable=True)
    grid = Column(Integer)
    position = Column(Integer, nullable=True)
    position_text = Column(String(10))
    position_order = Column(Integer)
    points = Column(Float)
    laps = Column(Integer)
    time = Column(String(50), nullable=True)
    milliseconds = Column(Integer, nullable=True)
    fastest_lap = Column(Integer, nullable=True)
    rank = Column(Integer, nullable=True)
    fastest_lap_time = Column(String(50), nullable=True)
    fastest_lap_speed = Column(Float, nullable=True)
    status_id = Column(Integer, ForeignKey("status.status_id"), nullable=False)

    race = relationship("Race", back_populates="results")
    driver = relationship("Driver", back_populates="results")
    constructor = relationship("Constructor", back_populates="results")
    status_info = relationship("Status", back_populates="results")


class Qualifying(Base):
    __tablename__ = "qualifying"

    qualify_id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey("races.race_id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"), nullable=False, index=True)
    constructor_id = Column(Integer, ForeignKey("constructors.constructor_id"), nullable=False)
    number = Column(Integer, nullable=True)
    position = Column(Integer, nullable=True)
    q1 = Column(String(50), nullable=True)
    q2 = Column(String(50), nullable=True)
    q3 = Column(String(50), nullable=True)

    race = relationship("Race", back_populates="qualifying_results")
    driver = relationship("Driver", back_populates="qualifying_results")
    constructor = relationship("Constructor", back_populates="qualifying_results")


class PitStop(Base):
    __tablename__ = "pit_stops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.race_id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"), nullable=False)
    stop = Column(Integer)
    lap = Column(Integer)
    time = Column(String(50), nullable=True)
    duration = Column(String(50), nullable=True)
    milliseconds = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_pit_stops_race_driver", "race_id", "driver_id"),
    )

    race = relationship("Race", back_populates="pit_stops")
    driver = relationship("Driver", back_populates="pit_stops")


class LapTime(Base):
    __tablename__ = "lap_times"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.race_id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"), nullable=False)
    lap = Column(Integer)
    position = Column(Integer, nullable=True)
    time = Column(String(50), nullable=True)
    milliseconds = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_lap_times_race_driver", "race_id", "driver_id"),
    )

    race = relationship("Race", back_populates="lap_times")
    driver = relationship("Driver", back_populates="lap_times")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # "user" or "admin"
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
