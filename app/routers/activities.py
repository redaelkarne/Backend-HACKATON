import json
from datetime import datetime, timezone
from typing import Optional

import gpxpy
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.models import Activity, Bike, User
from app.schemas.activities import (
    ActivityCompleteRequest, ActivityCreateRequest, ActivityOut, ActivityUpdateRequest, RouteOut,
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


@router.get("/{activityId}/route", response_model=ApiResponse[RouteOut])
async def get_activity_route(
    activityId: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Return the GPS coordinates of an activity as a parsed array,
    ready to pass directly to Leaflet or any OpenStreetMap renderer.

    Example frontend usage:
        const { coordinates } = data;
        L.polyline(coordinates).addTo(map);
    """
    result = await db.execute(select(Activity).where(Activity.id == activityId))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if not activity.route_polyline:
        raise HTTPException(status_code=404, detail="No route data for this activity")

    try:
        coordinates = json.loads(activity.route_polyline)
    except (ValueError, TypeError):
        raise HTTPException(status_code=500, detail="Route data is corrupted")

    return ApiResponse(
        data=RouteOut(
            activity_id=activity.id,
            coordinates=coordinates,
            distance_km=activity.distance_km,
            elevation_m=activity.elevation_m,
            duration_seconds=activity.duration_seconds,
            average_speed_kmh=activity.average_speed_kmh,
            started_at=activity.started_at,
            completed_at=activity.completed_at,
        ),
        meta=build_meta(),
    )


@router.post("/import/gpx", response_model=ApiResponse[ActivityOut], status_code=201)
async def import_gpx(
    file: UploadFile = File(..., description="GPX file exported from any GPS device or OpenStreetMap tool"),
    bike_id: Optional[str] = Query(None, description="Bike to associate. Defaults to your first bike."),
    type: str = Query("route", description="Activity type: route, gravel, mtb, urban"),
    weather: Optional[str] = Query(None, description="Weather conditions: dry, wet, mixed"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Import a GPX file as a completed activity.
    Distance, duration, elevation gain, average speed and route polyline
    are all computed automatically from the track points.
    """
    if not file.filename or not file.filename.lower().endswith(".gpx"):
        raise HTTPException(status_code=422, detail="File must be a .gpx file")

    content = await file.read()
    try:
        gpx = gpxpy.parse(content.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid GPX file")

    if not gpx.tracks:
        raise HTTPException(status_code=422, detail="GPX file contains no tracks")

    # Resolve bike
    if bike_id:
        bike_result = await db.execute(
            select(Bike).where(Bike.id == bike_id, Bike.user_id == current_user.id)
        )
        if not bike_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Bike not found")
    else:
        first_bike = await db.execute(
            select(Bike).where(Bike.user_id == current_user.id).limit(1)
        )
        bike = first_bike.scalar_one_or_none()
        if not bike:
            raise HTTPException(
                status_code=400,
                detail="No bike on your profile. Add one first via POST /profiles/{userId}/bike.",
            )
        bike_id = bike.id

    # Extract stats
    moving_data = gpx.get_moving_data()
    uphill_gain = gpx.get_uphill_downhill().uphill if gpx.has_elevations() else None

    # get_moving_data() needs timestamps; fall back to length_2d() for timestamp-less routes
    raw_distance = moving_data.moving_distance or 0
    if raw_distance == 0:
        raw_distance = gpx.length_2d() or 0
    distance_km = round(raw_distance / 1000, 2)
    duration_seconds = int(moving_data.moving_time or 0)
    elevation_m = round(uphill_gain, 1) if uphill_gain is not None else None
    average_speed_kmh = round(distance_km / (duration_seconds / 3600), 2) if duration_seconds > 0 else 0

    time_bounds = gpx.get_time_bounds()
    started_at = time_bounds.start_time or datetime.now(timezone.utc)
    ended_at = time_bounds.end_time or started_at

    # Lightweight polyline: sample every 10th point as [[lat, lon], ...]
    coords = []
    for track in gpx.tracks:
        for segment in track.segments:
            for i, pt in enumerate(segment.points):
                if i % 10 == 0:
                    coords.append([round(pt.latitude, 6), round(pt.longitude, 6)])
    route_polyline = json.dumps(coords) if coords else None

    activity = Activity(
        user_id=current_user.id,
        bike_id=bike_id,
        type=type,
        status="completed",
        weather=weather,
        notes=file.filename,
        started_at=started_at,
        completed_at=ended_at,
        distance_km=distance_km,
        duration_seconds=duration_seconds,
        elevation_m=elevation_m,
        average_speed_kmh=average_speed_kmh,
        route_polyline=route_polyline,
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return ApiResponse(data=ActivityOut.model_validate(activity), meta=build_meta())
