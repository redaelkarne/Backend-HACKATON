from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class StravaConnectOut(BaseModel):
    auth_url: str
    message: str


class StravaConnectedOut(BaseModel):
    connected: bool
    athlete_id: str
    athlete_name: str


class StravaActivityPreview(BaseModel):
    strava_id: int
    name: str
    sport_type: str
    distance_km: float
    duration_seconds: int
    elevation_m: float
    started_at: datetime
    already_imported: bool = False


class StravaImportRequest(BaseModel):
    strava_activity_id: int
    bike_id: Optional[str] = None
    type: Literal["route", "gravel", "mtb", "urban"] = "route"
    weather: Optional[Literal["dry", "wet", "mixed"]] = None
