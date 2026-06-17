from typing import List, Optional

from pydantic import BaseModel


class Preferences(BaseModel):
    terrains: Optional[List[str]] = None
    priorities: Optional[List[str]] = None
    weather_preferences: Optional[List[str]] = None


class ProfileStats(BaseModel):
    total_km: float
    total_rides: int
    level: int


class ProfileOut(BaseModel):
    user_id: str
    avatar_url: Optional[str] = None
    rider_type: str
    bio: Optional[str] = None
    preferences: Optional[Preferences] = None
    stats: Optional[ProfileStats] = None


class ProfileUpdateRequest(BaseModel):
    avatar_url: Optional[str] = None
    rider_type: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[Preferences] = None


class BikeCreateRequest(BaseModel):
    brand: str
    model: str
    category: str
    wheel_size: Optional[str] = None


class BikeOut(BaseModel):
    id: str
    user_id: str
    brand: str
    model: str
    category: str
    wheel_size: Optional[str] = None

    model_config = {"from_attributes": True}


class MountedTyreCreateRequest(BaseModel):
    bike_id: str
    brand: str
    model: str
    size: str
    mounted_at: str
    estimated_lifespan_km: float


class MountedTyreOut(BaseModel):
    id: str
    bike_id: str
    brand: str
    model: str
    size: str
    mounted_at: str
    estimated_lifespan_km: float
    catalogue_id: Optional[int] = None
    pic1: Optional[str] = None
    pic2: Optional[str] = None

    model_config = {"from_attributes": True}


class BikeWithTyresOut(BaseModel):
    id: str
    user_id: str
    brand: str
    model: str
    category: str
    wheel_size: Optional[str] = None
    mounted_tyres: List[MountedTyreOut] = []

    model_config = {"from_attributes": True}


class BikesListData(BaseModel):
    items: List[BikeWithTyresOut]
