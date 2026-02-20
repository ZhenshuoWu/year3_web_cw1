from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional


# ==================== Auth Schemas ====================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ==================== Driver Schemas ====================

class DriverBase(BaseModel):
    driver_ref: str
    number: Optional[int] = None
    code: Optional[str] = None
    forename: str
    surname: str
    dob: Optional[date] = None
    nationality: Optional[str] = None
    url: Optional[str] = None


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    number: Optional[int] = None
    code: Optional[str] = None
    forename: Optional[str] = None
    surname: Optional[str] = None
    nationality: Optional[str] = None
    url: Optional[str] = None


class DriverResponse(DriverBase):
    driver_id: int

    class Config:
        from_attributes = True


# ==================== Constructor Schemas ====================

class ConstructorBase(BaseModel):
    constructor_ref: str
    name: str
    nationality: Optional[str] = None
    url: Optional[str] = None


class ConstructorCreate(ConstructorBase):
    pass


class ConstructorUpdate(BaseModel):
    name: Optional[str] = None
    nationality: Optional[str] = None
    url: Optional[str] = None


class ConstructorResponse(ConstructorBase):
    constructor_id: int

    class Config:
        from_attributes = True


# ==================== Circuit Schemas ====================

class CircuitBase(BaseModel):
    circuit_ref: str
    name: str
    location: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    alt: Optional[float] = None
    url: Optional[str] = None


class CircuitCreate(CircuitBase):
    pass


class CircuitUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    url: Optional[str] = None


class CircuitResponse(CircuitBase):
    circuit_id: int

    class Config:
        from_attributes = True


# ==================== Race Schemas ====================

class RaceBase(BaseModel):
    year: int
    round: int
    circuit_id: int
    name: str
    date: Optional[date] = None
    url: Optional[str] = None


class RaceCreate(RaceBase):
    pass


class RaceResponse(RaceBase):
    race_id: int
    circuit: Optional[CircuitResponse] = None

    class Config:
        from_attributes = True


# ==================== Result Schemas ====================

class ResultResponse(BaseModel):
    result_id: int
    race_id: int
    driver_id: int
    constructor_id: int
    grid: Optional[int] = None
    position: Optional[int] = None
    position_text: Optional[str] = None
    points: Optional[float] = None
    laps: Optional[int] = None
    time: Optional[str] = None
    fastest_lap_time: Optional[str] = None
    fastest_lap_speed: Optional[float] = None
    status_id: int

    class Config:
        from_attributes = True


# ==================== Pagination ====================

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
