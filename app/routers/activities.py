from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.models import Activity, User
from app.schemas.activities import (
    ActivityCompleteRequest, ActivityCreateRequest, ActivityOut, ActivityUpdateRequest,
)
from app.schemas.common import ApiResponse, build_meta

router = APIRouter(prefix="/activities", tags=["Activities"])


@router.post("", response_model=ApiResponse[ActivityOut], status_code=201)
async def create_activity(
    body: ActivityCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    activity = Activity(
        user_id=current_user.id,
        bike_id=body.bike_id,
        type=body.type,
        started_at=body.started_at,
        weather=body.weather,
        notes=body.notes,
        status="draft",
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return ApiResponse(data=ActivityOut.model_validate(activity), meta=build_meta())


@router.get("", response_model=ApiResponse[dict])
async def list_activities(
    user_id: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    query = select(Activity)
    if user_id:
        query = query.where(Activity.user_id == user_id)
    query = query.order_by(Activity.started_at.desc()).limit(limit)
    result = await db.execute(query)
    activities = result.scalars().all()
    items = [ActivityOut.model_validate(a) for a in activities]
    return ApiResponse(
        data={"items": items},
        meta=build_meta(total=len(items)),
    )


@router.get("/{activityId}", response_model=ApiResponse[ActivityOut])
async def get_activity(activityId: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Activity).where(Activity.id == activityId))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return ApiResponse(data=ActivityOut.model_validate(activity), meta=build_meta())


@router.patch("/{activityId}", response_model=ApiResponse[ActivityOut])
async def update_activity(
    activityId: str,
    body: ActivityUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Activity).where(Activity.id == activityId))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if body.weather is not None:
        activity.weather = body.weather
    if body.notes is not None:
        activity.notes = body.notes

    await db.commit()
    await db.refresh(activity)
    return ApiResponse(data=ActivityOut.model_validate(activity), meta=build_meta())


@router.post("/{activityId}/complete", response_model=ApiResponse[ActivityOut])
async def complete_activity(
    activityId: str,
    body: ActivityCompleteRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Activity).where(Activity.id == activityId))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity.status = "completed"
    activity.completed_at = datetime.now(timezone.utc)
    activity.distance_km = body.distance_km
    activity.duration_seconds = body.duration_seconds
    activity.elevation_m = body.elevation_m
    activity.average_speed_kmh = body.average_speed_kmh
    activity.route_polyline = body.route_polyline

    await db.commit()
    await db.refresh(activity)
    return ApiResponse(data=ActivityOut.model_validate(activity), meta=build_meta())
