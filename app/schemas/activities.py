from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ActivityCreateRequest(BaseModel):
    user_id: str
    bike_id: str
    type: str
    started_at: datetime
    weather: Optional[str] = None
    notes: Optional[str] = None


class ActivityUpdateRequest(BaseModel):
    weather: Optional[str] = None
    notes: Optional[str] = None


class ActivityCompleteRequest(BaseModel):
    distance_km: float
    duration_seconds: int
    elevation_m: float
    average_speed_kmh: float
    route_polyline: Optional[str] = None


class ActivityOut(BaseModel):
    id: str
    user_id: str
    bike_id: str
    type: str
    status: str
    weather: Optional[str] = None
    notes: Optional[str] = None
    distance_km: Optional[float] = None
    duration_seconds: Optional[int] = None
    elevation_m: Optional[float] = None
    average_speed_kmh: Optional[float] = None
    route_polyline: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RouteOut(BaseModel):
    activity_id: str
    coordinates: List[List[float]]  # [[lat, lon], ...]
    distance_km: Optional[float]
    elevation_m: Optional[float]
    duration_seconds: Optional[int]
    average_speed_kmh: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
