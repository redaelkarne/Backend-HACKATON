from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.catalogue import find_best_tyres, lookup_tyre_db
from app.core.security import get_current_user
from app.database import get_db
from app.models.models import TyreRecommendation, User
from app.schemas.common import ApiResponse, build_meta
from app.schemas.recommendations import TyreCandidate, TyreRecommendationPayload, TyreRecommendationRequest

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/tyres", response_model=ApiResponse[TyreRecommendationPayload], status_code=201)
async def create_recommendation(
    body: TyreRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = find_best_tyres(
        bike_type=body.bike_type,
        riding_style=body.riding_style,
        terrain=body.terrain,
        budget_level=body.budget_level,
        tubeless=body.tubeless,
        e_bike=body.e_bike,
    )

    if not results:
        raise HTTPException(status_code=404, detail="No tyre found for these criteria")

    primary_data = dict(results[0])
    catalogue_info = await lookup_tyre_db(primary_data.get("model", ""), db)
    primary = TyreCandidate(**{**primary_data, "id": catalogue_info["catalogue_id"]})
    alternatives = [TyreCandidate(**t) for t in results[1:]]

    rec = TyreRecommendation(
        user_id=current_user.id,
        rider_type=body.bike_type,
        terrain=body.terrain,
        weather=body.riding_style,
        priority=body.budget_level,
        ride_frequency="tubeless" if body.tubeless else "tube",
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

    primary_stored = dict(rec.primary_tyre or {})
    catalogue_info = await lookup_tyre_db(primary_stored.get("model", ""), db)
    primary_tyre = TyreCandidate(**{**primary_stored, "id": catalogue_info["catalogue_id"]})

    return ApiResponse(
        data=TyreRecommendationPayload(
            recommendation_id=rec.id,
            primary_tyre=primary_tyre,
            alternatives=[TyreCandidate(**a) for a in (rec.alternatives or [])],
        ),
        meta=build_meta(),
    )
