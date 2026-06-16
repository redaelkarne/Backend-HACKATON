from typing import List, Optional

from pydantic import BaseModel


class TyreRecommendationRequest(BaseModel):
    rider_type: str
    terrain: str
    weather: str
    priority: str
    ride_frequency: str


class TyreCandidate(BaseModel):
    brand: str
    model: str
    category: str
    reasons: Optional[List[str]] = None


class TyreRecommendationPayload(BaseModel):
    recommendation_id: str
    primary_tyre: TyreCandidate
    alternatives: List[TyreCandidate] = []
