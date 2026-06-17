from typing import List, Optional

from pydantic import BaseModel


class ProgressSummary(BaseModel):
    total_km: float
    total_rides: int
    weekly_km: float
    monthly_km: float
    badges_count: int


class WeeklyDay(BaseModel):
    day: str
    distance_km: float


class WeeklyData(BaseModel):
    days: List[WeeklyDay]


class TyreWearItem(BaseModel):
    mounted_tyre_id: str
    tyre_name: str
    distance_done_km: float
    estimated_lifespan_km: float
    wear_percent: float
    replacement_status: str
    catalogue_id: Optional[int] = None
    pic1: Optional[str] = None
    pic2: Optional[str] = None


class TyreWearData(BaseModel):
    items: List[TyreWearItem]
