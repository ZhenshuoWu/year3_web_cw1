from pydantic import BaseModel, Field, ConfigDict
import datetime
from typing import Optional, Any, Union


# ==================== Auth Schemas ====================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username", examples=["lewis_h"])
    email: str = Field(..., max_length=255, description="User email address", examples=["lewis@example.com"])
    password: str = Field(..., min_length=6, description="Password (min 6 characters)", examples=["securePass123"])

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "username": "lewis_h",
            "email": "lewis@example.com",
            "password": "securePass123"
        }
    })


class UserResponse(BaseModel):
    id: int = Field(..., description="User ID", examples=[1])
    username: str = Field(..., description="Username", examples=["lewis_h"])
    email: str = Field(..., description="Email address", examples=["lewis@example.com"])
    role: str = Field(..., description="User role: 'user' or 'admin'", examples=["user"])

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token", examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])
    token_type: str = Field(default="bearer", description="Token type", examples=["bearer"])


# ==================== Driver Schemas ====================

class DriverBase(BaseModel):
    driver_ref: str = Field(..., description="Unique driver reference identifier", examples=["hamilton"])
    number: Optional[int] = Field(None, description="Permanent racing number", examples=[44])
    code: Optional[str] = Field(None, description="Three-letter driver code", examples=["HAM"])
    forename: str = Field(..., description="Driver first name", examples=["Lewis"])
    surname: str = Field(..., description="Driver last name", examples=["Hamilton"])
    dob: Optional[datetime.date] = Field(None, description="Date of birth (YYYY-MM-DD)", examples=["1985-01-07"])
    nationality: Optional[str] = Field(None, description="Driver nationality", examples=["British"])
    url: Optional[str] = Field(None, description="Wikipedia URL", examples=["http://en.wikipedia.org/wiki/Lewis_Hamilton"])


class DriverCreate(DriverBase):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "driver_ref": "hamilton",
            "number": 44,
            "code": "HAM",
            "forename": "Lewis",
            "surname": "Hamilton",
            "dob": "1985-01-07",
            "nationality": "British",
            "url": "http://en.wikipedia.org/wiki/Lewis_Hamilton"
        }
    })


class DriverUpdate(BaseModel):
    number: Optional[int] = Field(None, description="Permanent racing number", examples=[44])
    code: Optional[str] = Field(None, description="Three-letter driver code", examples=["HAM"])
    forename: Optional[str] = Field(None, description="Driver first name", examples=["Lewis"])
    surname: Optional[str] = Field(None, description="Driver last name", examples=["Hamilton"])
    nationality: Optional[str] = Field(None, description="Driver nationality", examples=["British"])
    url: Optional[str] = Field(None, description="Wikipedia URL")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "number": 44,
            "nationality": "British"
        }
    })


class DriverResponse(DriverBase):
    driver_id: int = Field(..., description="Unique driver ID", examples=[1])

    model_config = ConfigDict(from_attributes=True)


# ==================== Constructor Schemas ====================

class ConstructorBase(BaseModel):
    constructor_ref: str = Field(..., description="Unique constructor reference", examples=["mercedes"])
    name: str = Field(..., description="Constructor team name", examples=["Mercedes"])
    nationality: Optional[str] = Field(None, description="Constructor nationality", examples=["German"])
    url: Optional[str] = Field(None, description="Wikipedia URL", examples=["http://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One"])


class ConstructorCreate(ConstructorBase):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "constructor_ref": "mercedes",
            "name": "Mercedes",
            "nationality": "German",
            "url": "http://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One"
        }
    })


class ConstructorUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Constructor team name", examples=["Mercedes"])
    nationality: Optional[str] = Field(None, description="Constructor nationality", examples=["German"])
    url: Optional[str] = Field(None, description="Wikipedia URL")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Mercedes AMG Petronas",
            "nationality": "German"
        }
    })


class ConstructorResponse(ConstructorBase):
    constructor_id: int = Field(..., description="Unique constructor ID", examples=[1])

    model_config = ConfigDict(from_attributes=True)


class ConstructorListResponse(ConstructorResponse):
    total_points: float = Field(..., description="All-time total championship points", examples=[7005.5])
    wins: int = Field(..., description="Total race victories", examples=[125])


# ==================== Circuit Schemas ====================

class CircuitBase(BaseModel):
    circuit_ref: str = Field(..., description="Unique circuit reference", examples=["silverstone"])
    name: str = Field(..., description="Official circuit name", examples=["Silverstone Circuit"])
    location: Optional[str] = Field(None, description="City or locality", examples=["Silverstone"])
    country: Optional[str] = Field(None, description="Country", examples=["UK"])
    lat: Optional[float] = Field(None, description="Latitude coordinate", examples=[52.0786])
    lng: Optional[float] = Field(None, description="Longitude coordinate", examples=[-1.01694])
    alt: Optional[float] = Field(None, description="Altitude in meters above sea level", examples=[153.0])
    url: Optional[str] = Field(None, description="Wikipedia URL", examples=["http://en.wikipedia.org/wiki/Silverstone_Circuit"])


class CircuitCreate(CircuitBase):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "circuit_ref": "silverstone",
            "name": "Silverstone Circuit",
            "location": "Silverstone",
            "country": "UK",
            "lat": 52.0786,
            "lng": -1.01694,
            "alt": 153.0,
            "url": "http://en.wikipedia.org/wiki/Silverstone_Circuit"
        }
    })


class CircuitUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Official circuit name", examples=["Silverstone Circuit"])
    location: Optional[str] = Field(None, description="City or locality", examples=["Silverstone"])
    country: Optional[str] = Field(None, description="Country", examples=["UK"])
    lat: Optional[float] = Field(None, description="Latitude coordinate", examples=[52.0786])
    lng: Optional[float] = Field(None, description="Longitude coordinate", examples=[-1.01694])
    alt: Optional[float] = Field(None, description="Altitude in meters", examples=[153.0])
    url: Optional[str] = Field(None, description="Wikipedia URL")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Silverstone Circuit",
            "country": "UK"
        }
    })


class CircuitResponse(CircuitBase):
    circuit_id: int = Field(..., description="Unique circuit ID", examples=[9])

    model_config = ConfigDict(from_attributes=True)


class CircuitListResponse(CircuitResponse):
    total_races: int = Field(..., description="Total number of races held at this circuit", examples=[59])


# ==================== Race Schemas ====================

class RaceBase(BaseModel):
    year: int = Field(..., description="Season year", examples=[2024])
    round: int = Field(..., description="Round number within season", examples=[12])
    circuit_id: int = Field(..., description="Circuit ID (foreign key)", examples=[9])
    name: str = Field(..., description="Grand Prix name", examples=["British Grand Prix"])
    date: Optional[datetime.date] = Field(None, description="Race date", examples=["2024-07-07"])
    url: Optional[str] = Field(None, description="Wikipedia URL")


class RaceCreate(RaceBase):
    pass


class RaceResponse(RaceBase):
    race_id: int = Field(..., description="Unique race ID", examples=[1100])
    circuit: Optional[CircuitResponse] = Field(None, description="Associated circuit details")

    model_config = ConfigDict(from_attributes=True)


# ==================== Result Schemas ====================

class ResultResponse(BaseModel):
    result_id: int = Field(..., description="Unique result ID", examples=[1])
    race_id: int = Field(..., description="Associated race ID", examples=[1100])
    driver_id: int = Field(..., description="Driver ID", examples=[1])
    constructor_id: int = Field(..., description="Constructor ID", examples=[1])
    grid: Optional[int] = Field(None, description="Starting grid position", examples=[1])
    position: Optional[int] = Field(None, description="Finishing position (null if DNF)", examples=[1])
    position_text: Optional[str] = Field(None, description="Position as text ('R' = retired)", examples=["1"])
    points: Optional[float] = Field(None, description="Points scored", examples=[25.0])
    laps: Optional[int] = Field(None, description="Laps completed", examples=[52])
    time: Optional[str] = Field(None, description="Finishing time or gap to winner", examples=["+5.856"])
    fastest_lap_time: Optional[str] = Field(None, description="Fastest lap time", examples=["1:27.097"])
    fastest_lap_speed: Optional[float] = Field(None, description="Fastest lap speed in km/h", examples=[236.452])
    status_id: int = Field(..., description="Race status ID (1 = Finished)", examples=[1])

    model_config = ConfigDict(from_attributes=True)


# ==================== Pagination ====================

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number (starts from 1)", examples=[1])
    per_page: int = Field(default=20, ge=1, le=100, description="Number of items per page", examples=[20])


# ==================== Circuit Detail Response ====================

class CircuitRaceEntry(BaseModel):
    """A recent race held at a circuit, including the winner."""
    race_id: int = Field(..., description="Race ID", examples=[1100])
    year: int = Field(..., description="Season year", examples=[2024])
    round: int = Field(..., description="Round number", examples=[12])
    race_name: str = Field(..., description="Grand Prix name", examples=["British Grand Prix"])
    date: Optional[str] = Field(None, description="Race date (YYYY-MM-DD)", examples=["2024-07-07"])
    winner: str = Field(..., description="Race winner full name", examples=["Lewis Hamilton"])


class CircuitDetailResponse(BaseModel):
    """Circuit details with race history and aggregated stats."""
    circuit_id: int = Field(..., description="Circuit ID", examples=[9])
    circuit_ref: str = Field(..., description="Circuit reference", examples=["silverstone"])
    name: str = Field(..., description="Circuit name", examples=["Silverstone Circuit"])
    location: Optional[str] = Field(None, description="City/location", examples=["Silverstone"])
    country: Optional[str] = Field(None, description="Country", examples=["UK"])
    lat: Optional[float] = Field(None, description="Latitude", examples=[52.0786])
    lng: Optional[float] = Field(None, description="Longitude", examples=[-1.01694])
    alt: Optional[float] = Field(None, description="Altitude in meters", examples=[153.0])
    url: Optional[str] = Field(None, description="Wikipedia URL")
    total_races_held: int = Field(..., description="Total races held at this circuit", examples=[59])
    recent_races: list[CircuitRaceEntry] = Field(..., description="5 most recent races with winners")


# ==================== Constructor Detail Response ====================

class ConstructorCareerSummary(BaseModel):
    """Aggregated career statistics for a constructor."""
    total_entries: int = Field(..., description="Total race entries", examples=[268])
    total_points: float = Field(..., description="All-time total points", examples=[7005.5])
    wins: int = Field(..., description="Total victories", examples=[125])
    podiums: int = Field(..., description="Total podium finishes", examples=[275])
    first_season: Optional[int] = Field(None, description="First season competed", examples=[2010])
    last_season: Optional[int] = Field(None, description="Most recent season", examples=[2024])


class ConstructorTopDriver(BaseModel):
    """A top-performing driver for a constructor."""
    driver: str = Field(..., description="Driver full name", examples=["Lewis Hamilton"])
    races_for_team: int = Field(..., description="Races driven for this team", examples=[192])
    points_for_team: float = Field(..., description="Points scored for this team", examples=[2560.5])
    wins_for_team: int = Field(..., description="Wins with this team", examples=[84])


class ConstructorDetailResponse(BaseModel):
    """Constructor details with career summary and notable drivers."""
    constructor_id: int = Field(..., description="Constructor ID", examples=[1])
    constructor_ref: str = Field(..., description="Constructor reference", examples=["mercedes"])
    name: str = Field(..., description="Constructor name", examples=["Mercedes"])
    nationality: Optional[str] = Field(None, description="Nationality", examples=["German"])
    url: Optional[str] = Field(None, description="Wikipedia URL")
    career_summary: ConstructorCareerSummary = Field(..., description="Aggregated career statistics")
    top_drivers: list[ConstructorTopDriver] = Field(..., description="Top 5 drivers by points for this team")


# ==================== Analytics: Career Stats ====================

class DriverCareerInfo(BaseModel):
    """Basic driver identification."""
    id: int = Field(..., description="Driver ID", examples=[1])
    name: str = Field(..., description="Full name", examples=["Lewis Hamilton"])
    nationality: Optional[str] = Field(None, description="Nationality", examples=["British"])


class CareerStatistics(BaseModel):
    """Comprehensive career statistics."""
    total_races: int = Field(..., description="Total race entries", examples=[340])
    wins: int = Field(..., description="Total wins", examples=[103])
    podiums: int = Field(..., description="Total podium finishes (top 3)", examples=[197])
    pole_positions: int = Field(..., description="Total pole positions", examples=[104])
    total_points: float = Field(..., description="Total career points", examples=[4639.5])
    dnfs: int = Field(..., description="Did Not Finish count", examples=[30])
    best_finish: Optional[int] = Field(None, description="Best finishing position", examples=[1])
    win_rate: float = Field(..., description="Win percentage", examples=[30.29])
    podium_rate: float = Field(..., description="Podium percentage", examples=[57.94])


class CareerStatsResponse(BaseModel):
    """Full career statistics for a driver."""
    driver: DriverCareerInfo = Field(..., description="Driver identification")
    career: CareerStatistics = Field(..., description="Career statistics")
    teams: list[str] = Field(..., description="Constructors driven for", examples=[["McLaren", "Mercedes", "Ferrari"]])
    seasons: list[int] = Field(..., description="Active seasons list")


# ==================== Analytics: Season Progression ====================

class RoundProgressEntry(BaseModel):
    """Single round in a season progression."""
    round: int = Field(..., description="Round number", examples=[1])
    race_name: str = Field(..., description="Grand Prix name", examples=["Bahrain Grand Prix"])
    position: Optional[int] = Field(None, description="Finishing position", examples=[1])
    points_scored: float = Field(..., description="Points earned this round", examples=[25.0])
    cumulative_points: float = Field(..., description="Running total points", examples=[25.0])


class SeasonProgressionResponse(BaseModel):
    """A driver's round-by-round points accumulation across a season."""
    driver: str = Field(..., description="Driver full name", examples=["Lewis Hamilton"])
    season: int = Field(..., description="Season year", examples=[2020])
    total_points: float = Field(..., description="Total season points", examples=[347.0])
    rounds: list[RoundProgressEntry] = Field(..., description="Round-by-round progression data")


# ==================== Analytics: Driver Compare ====================

class DriverCompareStats(BaseModel):
    """Statistics for a driver in a comparison."""
    total_races: int = Field(..., description="Total races", examples=[340])
    wins: int = Field(..., description="Total wins", examples=[103])
    podiums: int = Field(..., description="Total podiums", examples=[197])
    total_points: float = Field(..., description="Total points", examples=[4639.5])
    dnfs: int = Field(..., description="DNF count", examples=[30])
    avg_finish: float = Field(..., description="Average finishing position", examples=[4.52])


class DriverCompareEntry(BaseModel):
    """A driver entry in a head-to-head comparison."""
    name: str = Field(..., description="Driver full name", examples=["Lewis Hamilton"])
    stats: DriverCompareStats


class HeadToHeadResult(BaseModel):
    """Head-to-head finishing results between two drivers."""
    common_races: int = Field(..., description="Races both drivers entered", examples=[200])
    driver_1_ahead: int = Field(..., description="Races driver 1 finished ahead", examples=[110])
    driver_2_ahead: int = Field(..., description="Races driver 2 finished ahead", examples=[85])


class DriverCompareResponse(BaseModel):
    """Head-to-head comparison between two drivers."""
    driver_1: DriverCompareEntry
    driver_2: DriverCompareEntry
    head_to_head: HeadToHeadResult
    season_filter: Optional[int] = Field(None, description="Applied season filter", examples=[2020])


# ==================== Analytics: Pit Stop Analysis ====================

class PitStopDetailEntry(BaseModel):
    """Individual pit stop record."""
    stop: int = Field(..., description="Stop number (1st, 2nd, etc.)", examples=[1])
    lap: int = Field(..., description="Lap number of the stop", examples=[18])
    duration: Optional[str] = Field(None, description="Pit stop duration as string", examples=["23.140"])
    milliseconds: Optional[int] = Field(None, description="Duration in milliseconds", examples=[23140])


class DriverPitStopAnalysis(BaseModel):
    """Pit stop data for a single driver in a race."""
    driver: str = Field(..., description="Driver full name", examples=["Lewis Hamilton"])
    grid_position: Optional[int] = Field(None, description="Starting grid position", examples=[1])
    final_position: Optional[int] = Field(None, description="Final race position", examples=[1])
    num_stops: int = Field(..., description="Number of pit stops", examples=[2])
    total_pit_time_ms: int = Field(..., description="Total time spent in pits (ms)", examples=[46280])
    stops_detail: list[PitStopDetailEntry] = Field(..., description="Individual pit stop details")


class StrategyStats(BaseModel):
    """Statistics for a pit stop strategy (e.g. 1-stop, 2-stop)."""
    drivers: int = Field(..., description="Number of drivers using this strategy", examples=[12])
    avg_finish_position: Optional[float] = Field(None, description="Average finishing position", examples=[6.5])


class PitStopAnalysisResponse(BaseModel):
    """Pit stop strategy analysis for a specific race."""
    race: str = Field(..., description="Race name", examples=["British Grand Prix"])
    season: int = Field(..., description="Season year", examples=[2024])
    strategy_summary: dict[str, StrategyStats] = Field(
        ..., description="Summary by stop count (keys: '0_stop', '1_stop', '2_stop', etc.)"
    )
    driver_details: list[DriverPitStopAnalysis] = Field(
        ..., description="Per-driver pit stop analysis, sorted by finishing position"
    )


# ==================== Analytics: Circuit History ====================

class CircuitHistoryInfo(BaseModel):
    """Basic circuit identification for history response."""
    name: str = Field(..., description="Circuit name", examples=["Silverstone Circuit"])
    location: Optional[str] = Field(None, description="Location", examples=["Silverstone"])
    country: Optional[str] = Field(None, description="Country", examples=["UK"])


class CircuitHistoryStats(BaseModel):
    """Historical statistics for a circuit."""
    total_races: int = Field(..., description="Total races held", examples=[59])
    first_race_year: int = Field(..., description="Year of first race", examples=[1950])
    last_race_year: int = Field(..., description="Year of most recent race", examples=[2024])


class CircuitWinnerEntry(BaseModel):
    """A top-winning driver at a specific circuit."""
    driver: str = Field(..., description="Driver full name", examples=["Lewis Hamilton"])
    wins: int = Field(..., description="Wins at this circuit", examples=[8])


class CircuitHistoryResponse(BaseModel):
    """Historical statistics and most successful drivers at a circuit."""
    circuit: CircuitHistoryInfo = Field(..., description="Circuit information")
    statistics: CircuitHistoryStats = Field(..., description="Historical statistics")
    most_successful_drivers: list[CircuitWinnerEntry] = Field(
        ..., description="Top 5 winningest drivers at this circuit"
    )


# ==================== Advanced Analytics: Win Probability ====================

class CircuitHistoryFactorDetail(BaseModel):
    """Detail for circuit history factor."""
    races_at_circuit: int = Field(..., description="Total races at this circuit", examples=[15])
    wins_at_circuit: int = Field(..., description="Wins at this circuit", examples=[8])
    podiums_at_circuit: int = Field(..., description="Podiums at this circuit", examples=[12])
    avg_finish_at_circuit: Optional[float] = Field(None, description="Average finish position here", examples=[2.3])


class RecentFormFactorDetail(BaseModel):
    """Detail for recent form factor."""
    last_5_races_avg_finish: Optional[float] = Field(None, description="Avg finish in last 5 races", examples=[3.2])
    last_5_wins: int = Field(..., description="Wins in last 5 races", examples=[2])
    last_5_podiums: int = Field(..., description="Podiums in last 5 races", examples=[4])


class GridConversionFactorDetail(BaseModel):
    """Detail for grid conversion factor."""
    front_row_starts: int = Field(..., description="Times started from front row", examples=[120])
    front_row_wins: int = Field(..., description="Wins from front row starts", examples=[65])


class CareerBaselineFactorDetail(BaseModel):
    """Detail for career baseline factor."""
    total_races: int = Field(..., description="Total career races", examples=[340])
    total_wins: int = Field(..., description="Total career wins", examples=[103])


class CircuitHistoryFactor(BaseModel):
    """Circuit history weighted factor (35%)."""
    weight: str = Field(..., description="Factor weight", examples=["35%"])
    score: float = Field(..., description="Factor score (0-100)", examples=[53.3])
    detail: CircuitHistoryFactorDetail


class RecentFormFactor(BaseModel):
    """Recent form weighted factor (30%)."""
    weight: str = Field(..., description="Factor weight", examples=["30%"])
    score: float = Field(..., description="Factor score (0-100)", examples=[72.1])
    detail: RecentFormFactorDetail


class GridConversionFactor(BaseModel):
    """Grid conversion weighted factor (20%)."""
    weight: str = Field(..., description="Factor weight", examples=["20%"])
    score: float = Field(..., description="Factor score (0-100)", examples=[54.2])
    detail: GridConversionFactorDetail


class CareerBaselineFactor(BaseModel):
    """Career baseline weighted factor (15%)."""
    weight: str = Field(..., description="Factor weight", examples=["15%"])
    score: float = Field(..., description="Factor score (0-100)", examples=[30.3])
    detail: CareerBaselineFactorDetail


class WinProbabilityFactors(BaseModel):
    """All four weighted factors contributing to win probability."""
    circuit_history: CircuitHistoryFactor = Field(..., description="Historical performance at this circuit (35%)")
    recent_form: RecentFormFactor = Field(..., description="Recent form from last 5 races (30%)")
    grid_conversion: GridConversionFactor = Field(..., description="Front row to win conversion rate (20%)")
    career_baseline: CareerBaselineFactor = Field(..., description="Overall career win rate (15%)")


class WinProbabilityResponse(BaseModel):
    """Win probability prediction with weighted factor breakdown."""
    driver: str = Field(..., description="Driver full name", examples=["Lewis Hamilton"])
    circuit: str = Field(..., description="Circuit name", examples=["Silverstone Circuit"])
    win_probability: str = Field(..., description="Estimated win probability", examples=["32.5%"])
    factors: WinProbabilityFactors = Field(..., description="Weighted factor breakdown")
    note: str = Field(..., description="Methodology disclaimer")


# ==================== Advanced Analytics: Performance Summary ====================

class QualifyingPaceDetail(BaseModel):
    """Qualifying pace dimension detail."""
    avg_qualifying_position: Optional[float] = Field(None, description="Average qualifying position", examples=[3.2])
    pole_positions: int = Field(..., description="Total pole positions", examples=[104])
    top_3_qualifying: int = Field(..., description="Times qualified in top 3", examples=[250])


class RacePaceDetail(BaseModel):
    """Race pace dimension detail."""
    avg_finish_position: float = Field(..., description="Average finishing position", examples=[4.5])
    wins: int = Field(..., description="Total wins", examples=[103])
    podiums: int = Field(..., description="Total podiums", examples=[197])
    points_per_race: float = Field(..., description="Average points per race", examples=[13.6])


class ConsistencyDetail(BaseModel):
    """Consistency dimension detail."""
    finish_rate: str = Field(..., description="Race completion percentage", examples=["91.2%"])
    points_finish_rate: str = Field(..., description="Points-scoring race percentage", examples=["78.5%"])
    dnfs: int = Field(..., description="Total DNFs", examples=[30])


class OvertakingDetail(BaseModel):
    """Overtaking ability dimension detail."""
    avg_positions_gained: float = Field(..., description="Average positions gained per race", examples=[1.3])
    races_analysed: int = Field(..., description="Number of races with valid grid/finish data", examples=[310])


class PitStopEfficiencyDetail(BaseModel):
    """Pit stop efficiency dimension detail."""
    median_pit_time_ms: Optional[float] = Field(None, description="Median pit stop time in milliseconds", examples=[24500])
    total_pit_stops: int = Field(..., description="Total pit stops analysed", examples=[580])


class QualifyingPaceDimension(BaseModel):
    """Qualifying pace performance dimension (25%)."""
    score: float = Field(..., description="Dimension score (0-100)", examples=[85.3])
    weight: str = Field(..., description="Weight in overall rating", examples=["25%"])
    detail: QualifyingPaceDetail


class RacePaceDimension(BaseModel):
    """Race pace performance dimension (30%)."""
    score: float = Field(..., description="Dimension score (0-100)", examples=[81.6])
    weight: str = Field(..., description="Weight in overall rating", examples=["30%"])
    detail: RacePaceDetail


class ConsistencyDimension(BaseModel):
    """Consistency performance dimension (20%)."""
    score: float = Field(..., description="Dimension score (0-100)", examples=[78.9])
    weight: str = Field(..., description="Weight in overall rating", examples=["20%"])
    detail: ConsistencyDetail


class OvertakingDimension(BaseModel):
    """Overtaking ability performance dimension (15%)."""
    score: float = Field(..., description="Dimension score (0-100)", examples=[65.4])
    weight: str = Field(..., description="Weight in overall rating", examples=["15%"])
    detail: OvertakingDetail


class PitStopEfficiencyDimension(BaseModel):
    """Pit stop efficiency performance dimension (10%)."""
    score: float = Field(..., description="Dimension score (0-100)", examples=[75.0])
    weight: str = Field(..., description="Weight in overall rating", examples=["10%"])
    detail: PitStopEfficiencyDetail


class PerformanceDimensions(BaseModel):
    """All five performance dimensions."""
    qualifying_pace: QualifyingPaceDimension = Field(..., description="Qualifying performance (25%)")
    race_pace: RacePaceDimension = Field(..., description="Race finishing ability (30%)")
    consistency: ConsistencyDimension = Field(..., description="Finish rate and points consistency (20%)")
    overtaking: OvertakingDimension = Field(..., description="Position gain ability (15%)")
    pit_stop_efficiency: PitStopEfficiencyDimension = Field(..., description="Pit stop time efficiency (10%)")


class PerformanceSummaryResponse(BaseModel):
    """Multi-dimensional performance rating for a driver."""
    driver: str = Field(..., description="Driver full name", examples=["Lewis Hamilton"])
    season: Union[int, str] = Field(..., description="Season year or 'all-time'", examples=[2020])
    overall_rating: float = Field(..., description="Weighted overall rating (0-100)", examples=[82.5])
    total_races: int = Field(..., description="Races analysed", examples=[17])
    dimensions: PerformanceDimensions = Field(..., description="Five performance dimensions with scores")


# ==================== Advanced Analytics: Teammate Battle ====================

class BattleScore(BaseModel):
    """Head-to-head qualifying or race battle result."""
    driver_wins: int = Field(..., description="Times the driver finished ahead", examples=[12])
    teammate_wins: int = Field(..., description="Times the teammate finished ahead", examples=[8])
    winner: str = Field(..., description="Name of the winner or 'Tied'", examples=["Hamilton"])


class PointsBattleScore(BaseModel):
    """Points comparison between driver and teammate."""
    driver_points: float = Field(..., description="Driver's total points", examples=[347.0])
    teammate_points: float = Field(..., description="Teammate's total points", examples=[230.5])
    winner: str = Field(..., description="Points leader or 'Tied'", examples=["Hamilton"])


class TeammateBattleEntry(BaseModel):
    """Battle results against a single teammate."""
    constructor: str = Field(..., description="Team name", examples=["Mercedes"])
    teammate: str = Field(..., description="Teammate full name", examples=["Valtteri Bottas"])
    common_races: int = Field(..., description="Races both competed in", examples=[20])
    qualifying: BattleScore = Field(..., description="Qualifying head-to-head")
    race: BattleScore = Field(..., description="Race finishing head-to-head")
    points: PointsBattleScore = Field(..., description="Points comparison")


class TeammateBattleResponse(BaseModel):
    """Head-to-head comparison between a driver and their teammate(s) in a season."""
    driver: str = Field(..., description="Driver full name", examples=["Lewis Hamilton"])
    season: int = Field(..., description="Season year", examples=[2020])
    battles: list[TeammateBattleEntry] = Field(..., description="Battle results (one entry per teammate)")


# ==================== Advanced Analytics: Leaderboard ====================

class LeaderboardEntry(BaseModel):
    """A single entry in the leaderboard."""
    rank: int = Field(..., description="Position in leaderboard", examples=[1])
    driver: str = Field(..., description="Driver full name", examples=["Lewis Hamilton"])
    nationality: Optional[str] = Field(None, description="Nationality", examples=["British"])
    races: int = Field(..., description="Total races", examples=[340])
    wins: int = Field(..., description="Total wins", examples=[103])
    podiums: int = Field(..., description="Total podiums", examples=[197])
    total_points: float = Field(..., description="Total points scored", examples=[4639.5])
    win_rate: str = Field(..., description="Win percentage", examples=["30.3%"])


class LeaderboardResponse(BaseModel):
    """Dynamic leaderboard ranking drivers by a chosen metric."""
    season: Union[int, str] = Field(..., description="Season year or 'all-time'", examples=["all-time"])
    metric: str = Field(..., description="Ranking metric used", examples=["points"])
    total_drivers: int = Field(..., description="Number of drivers returned", examples=[20])
    leaderboard: list[LeaderboardEntry] = Field(..., description="Ranked driver entries")
