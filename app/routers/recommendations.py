from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.models import TyreRecommendation, User
from app.schemas.common import ApiResponse, build_meta
from app.schemas.recommendations import TyreCandidate, TyreRecommendationPayload, TyreRecommendationRequest

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

_CATALOGUE: dict = {
    ("route", "road", "dry", "performance"): ("Power Cup 2", ["Optimisé pour la performance sur route sèche", "Adapté aux longues distances", "Bonne efficacité de roulement"]),
    ("route", "road", "dry", "durability"): ("Power Endurance", ["Longue durée de vie", "Faible résistance au roulement"]),
    ("route", "road", "dry", "grip"): ("Power RS+", ["Grip maximal sur route sèche", "Excellente adhérence en courbe"]),
    ("route", "road", "dry", "puncture_protection"): ("Protek Cross Max", ["Protection anti-crevaison renforcée", "Robuste sur route"]),
    ("route", "road", "wet", "performance"): ("Power All Season", ["Performant par temps humide", "Adapté aux conditions mixtes"]),
    ("route", "road", "wet", "grip"): ("Power All Season", ["Grip fiable sur route mouillée", "Drainage efficace"]),
    ("route", "mixed", "performance"): ("Power All Season", ["Polyvalent toute saison", "Équilibre grip/durabilité"]),
    ("gravel", "mixed", "dry", "performance"): ("Power Gravel", ["Traction supérieure sur gravel", "Légèreté et robustesse"]),
    ("gravel", "trail", "mixed", "grip"): ("Power Gravel", ["Excellente adhérence sur sentiers", "Résistance aux coupures"]),
    ("mtb", "trail", "dry", "performance"): ("Wild Enduro", ["Grip exceptionnel en montagne", "Résistance aux chocs"]),
    ("mtb", "trail", "wet", "grip"): ("Wild Enduro", ["Drainage efficace sur sentiers humides", "Traction en descente"]),
    ("urban", "city", "dry", "durability"): ("City Grip 2", ["Longue durée de vie en ville", "Confort urbain"]),
    ("urban", "city", "wet", "grip"): ("City Grip 2", ["Sécurité par temps de pluie", "Silencieux sur bitume"]),
}

_ALTERNATIVES: dict = {
    "Power Cup 2": [TyreCandidate(brand="Michelin", model="Power RS+", category="route"), TyreCandidate(brand="Michelin", model="Power All Season", category="route")],
    "Power RS+": [TyreCandidate(brand="Michelin", model="Power Cup 2", category="route")],
    "Power All Season": [TyreCandidate(brand="Michelin", model="Power Endurance", category="route"), TyreCandidate(brand="Michelin", model="Power Cup 2", category="route")],
    "Power Endurance": [TyreCandidate(brand="Michelin", model="Power All Season", category="route")],
    "Protek Cross Max": [TyreCandidate(brand="Michelin", model="City Grip 2", category="urban")],
    "Power Gravel": [TyreCandidate(brand="Michelin", model="Power All Season", category="gravel")],
    "Wild Enduro": [TyreCandidate(brand="Michelin", model="Wild AM2", category="mtb")],
    "City Grip 2": [TyreCandidate(brand="Michelin", model="Protek Cross Max", category="urban")],
}

_CATEGORY_MAP = {"route": "route", "gravel": "gravel", "mtb": "mtb", "urban": "urban"}


def _recommend(req: TyreRecommendationRequest) -> tuple[str, list[str]]:
    keys_to_try = [
        (req.rider_type, req.terrain, req.weather, req.priority),
        (req.rider_type, req.terrain, req.weather),
        (req.rider_type, req.terrain, req.priority),
        (req.rider_type, req.weather, req.priority),
        (req.rider_type,),
    ]
    defaults = {
        "route": ("Power All Season", ["Polyvalent toutes conditions"]),
        "gravel": ("Power Gravel", ["Adapté au gravel"]),
        "mtb": ("Wild Enduro", ["VTT toutes conditions"]),
        "urban": ("City Grip 2", ["Idéal pour la ville"]),
    }
    for key in keys_to_try:
        if key in _CATALOGUE:
            return _CATALOGUE[key]
    return defaults.get(req.rider_type, ("Power All Season", ["Polyvalent"]))


@router.post("/tyres", response_model=ApiResponse[TyreRecommendationPayload], status_code=201)
async def create_recommendation(
    body: TyreRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model_name, reasons = _recommend(body)
    category = _CATEGORY_MAP.get(body.rider_type, "route")
    primary = TyreCandidate(brand="Michelin", model=model_name, category=category, reasons=reasons)
    alternatives = _ALTERNATIVES.get(model_name, [])

    rec = TyreRecommendation(
        user_id=current_user.id,
        rider_type=body.rider_type,
        terrain=body.terrain,
        weather=body.weather,
        priority=body.priority,
        ride_frequency=body.ride_frequency,
        primary_tyre=primary.model_dump(),
        alternatives=[a.model_dump() for a in alternatives],
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)

    return ApiResponse(
        data=TyreRecommendationPayload(
            recommendation_id=rec.id,
            primary_tyre=primary,
            alternatives=alternatives,
        ),
        meta=build_meta(),
    )


@router.get("/tyres/{recommendationId}", response_model=ApiResponse[TyreRecommendationPayload])
async def get_recommendation(
    recommendationId: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(TyreRecommendation).where(TyreRecommendation.id == recommendationId))
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return ApiResponse(
        data=TyreRecommendationPayload(
            recommendation_id=rec.id,
            primary_tyre=TyreCandidate(**rec.primary_tyre),
            alternatives=[TyreCandidate(**a) for a in (rec.alternatives or [])],
        ),
        meta=build_meta(),
    )
