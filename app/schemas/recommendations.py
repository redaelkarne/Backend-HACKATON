from typing import List, Literal, Optional

from pydantic import BaseModel


class TyreRecommendationRequest(BaseModel):
    rider_type: Literal["route", "gravel", "mtb", "urban"]
    terrain: Literal["road", "mixed", "trail", "city"]
    weather: Literal["dry", "wet", "mixed"] = "dry"
    priority: Literal["performance", "grip", "durability"] = "performance"
    ride_frequency: Literal["frequent", "regular", "occasional"] = "regular"


class TyreCandidate(BaseModel):
    id: Optional[int] = None
    brand: str
    model: str
    category: str
    segment: Optional[str] = None
    use: Optional[str] = None
    terrain_types: Optional[str] = None
    sealing: Optional[str] = None
    reasons: Optional[List[str]] = None
    product_url: Optional[str] = None
    pic1: Optional[str] = None
    pic2: Optional[str] = None


class TyreRecommendationPayload(BaseModel):
    recommendation_id: str
    primary_tyre: TyreCandidate
    alternatives: List[TyreCandidate] = []
