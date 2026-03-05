from typing import Literal, Optional

from pydantic import BaseModel


class DriverIdentity(BaseModel):
    id: int
    name: str
    nationality: Optional[str] = None


class DriverCareer(BaseModel):
    total_races: int
    wins: int
    podiums: int
    pole_positions: int
    total_points: float
    dnfs: int
    best_finish: Optional[int] = None
    win_rate: float
    podium_rate: float


class DriverCareerStatsResponse(BaseModel):
    driver: DriverIdentity
    career: DriverCareer
    teams: list[str]
    seasons: list[int]


class DriverSeasonRound(BaseModel):
    round: int
    race_name: str
    position: Optional[int] = None
    points_scored: float
    cumulative_points: float


class DriverSeasonProgressionResponse(BaseModel):
    driver: str
    season: int
    total_points: float
    rounds: list[DriverSeasonRound]


class DriverCompareStats(BaseModel):
    total_races: int
    wins: int
    podiums: int
    total_points: float
    dnfs: int
    avg_finish: float


class DriverCompareEntry(BaseModel):
    name: str
    stats: DriverCompareStats


class DriverCompareResponse(BaseModel):
    driver_1: DriverCompareEntry
    driver_2: DriverCompareEntry
    head_to_head: dict[str, int]
    season_filter: Optional[int] = None


class PitStopDetail(BaseModel):
    stop: Optional[int] = None
    lap: Optional[int] = None
    duration: Optional[str] = None
    milliseconds: Optional[int] = None


class PitStopDriverDetail(BaseModel):
    driver: str
    grid_position: Optional[int] = None
    final_position: Optional[int] = None
    num_stops: int
    total_pit_time_ms: int
    stops_detail: list[PitStopDetail]


class PitStopStrategySummary(BaseModel):
    drivers: int
    avg_finish_position: Optional[float] = None


class PitStopAnalysisResponse(BaseModel):
    race: str
    season: int
    strategy_summary: dict[str, PitStopStrategySummary]
    driver_details: list[PitStopDriverDetail]


class CircuitInfo(BaseModel):
    name: str
    location: Optional[str] = None
    country: Optional[str] = None


class CircuitStatistics(BaseModel):
    total_races: int
    first_race_year: int
    last_race_year: int


class CircuitTopDriver(BaseModel):
    driver: str
    wins: int


class CircuitHistoryResponse(BaseModel):
    circuit: CircuitInfo
    statistics: CircuitStatistics
    most_successful_drivers: list[CircuitTopDriver]


class WinProbabilityFactorDetail(BaseModel):
    races_at_circuit: Optional[int] = None
    wins_at_circuit: Optional[int] = None
    podiums_at_circuit: Optional[int] = None
    avg_finish_at_circuit: Optional[float] = None
    last_5_races_avg_finish: Optional[float] = None
    last_5_wins: Optional[int] = None
    last_5_podiums: Optional[int] = None
    front_row_starts: Optional[int] = None
    front_row_wins: Optional[int] = None
    total_races: Optional[int] = None
    total_wins: Optional[int] = None


class WinProbabilityFactor(BaseModel):
    weight: str
    score: float
    detail: WinProbabilityFactorDetail


class WinProbabilityFactors(BaseModel):
    circuit_history: WinProbabilityFactor
    recent_form: WinProbabilityFactor
    grid_conversion: WinProbabilityFactor
    career_baseline: WinProbabilityFactor


class WinProbabilityResponse(BaseModel):
    driver: str
    circuit: str
    win_probability: str
    factors: WinProbabilityFactors
    note: str


class PerformanceDimensionDetail(BaseModel):
    avg_qualifying_position: Optional[float] = None
    pole_positions: Optional[int] = None
    top_3_qualifying: Optional[int] = None
    avg_finish_position: Optional[float] = None
    wins: Optional[int] = None
    podiums: Optional[int] = None
    points_per_race: Optional[float] = None
    finish_rate: Optional[str] = None
    points_finish_rate: Optional[str] = None
    dnfs: Optional[int] = None
    avg_positions_gained: Optional[float] = None
    races_analysed: Optional[int] = None
    avg_pit_time_ms: Optional[int] = None
    total_pit_stops: Optional[int] = None


class PerformanceDimension(BaseModel):
    score: float
    weight: str
    detail: PerformanceDimensionDetail


class PerformanceDimensions(BaseModel):
    qualifying_pace: PerformanceDimension
    race_pace: PerformanceDimension
    consistency: PerformanceDimension
    overtaking: PerformanceDimension
    pit_stop_efficiency: PerformanceDimension


class PerformanceSummaryResponse(BaseModel):
    driver: str
    season: int | Literal["all-time"]
    overall_rating: float
    total_races: int
    dimensions: PerformanceDimensions


class TeammateBattleEntry(BaseModel):
    constructor: str
    teammate: str
    common_races: int
    qualifying: dict[str, int | str]
    race: dict[str, int | str]
    points: dict[str, float | str]


class TeammateBattleResponse(BaseModel):
    driver: str
    season: int
    battles: list[TeammateBattleEntry]


class LeaderboardEntry(BaseModel):
    rank: int
    driver: str
    nationality: Optional[str] = None
    races: int
    wins: int
    podiums: int
    total_points: float
    win_rate: str


class LeaderboardResponse(BaseModel):
    season: int | Literal["all-time"]
    metric: str
    total_drivers: int
    leaderboard: list[LeaderboardEntry]
