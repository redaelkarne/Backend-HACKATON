from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.catalogue import lookup_tyre_pics
from app.core.security import get_current_user
from app.database import get_db
from app.models.models import Activity, Bike, MountedTyre, User
from app.schemas.common import ApiResponse, build_meta
from app.schemas.progress import ProgressSummary, TyreWearData, TyreWearItem, WeeklyData, WeeklyDay

router = APIRouter(prefix="/progress", tags=["Progress"])

_DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


@router.get("/summary", response_model=ApiResponse[ProgressSummary])
async def progress_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    base = select(func.coalesce(func.sum(Activity.distance_km), 0)).where(
        Activity.user_id == current_user.id, Activity.status == "completed"
    )

    total_km = float((await db.execute(base)).scalar())
    total_rides = int((await db.execute(
        select(func.count(Activity.id)).where(Activity.user_id == current_user.id, Activity.status == "completed")
    )).scalar())
    weekly_km = float((await db.execute(base.where(Activity.completed_at >= week_start))).scalar())
    monthly_km = float((await db.execute(base.where(Activity.completed_at >= month_start))).scalar())

    badges = sum([
        1 if total_km >= 100 else 0,
        1 if total_km >= 500 else 0,
        1 if total_km >= 1000 else 0,
        1 if total_rides >= 10 else 0,
        1 if total_rides >= 50 else 0,
    ])

    return ApiResponse(
        data=ProgressSummary(
            total_km=round(total_km, 1),
            total_rides=total_rides,
            weekly_km=round(weekly_km, 1),
            monthly_km=round(monthly_km, 1),
            badges_count=badges,
        ),
        meta=build_meta(),
    )


@router.get("/weekly", response_model=ApiResponse[WeeklyData])
async def weekly_progress(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(Activity).where(
            Activity.user_id == current_user.id,
            Activity.status == "completed",
            Activity.completed_at >= week_start,
        )
    )
    activities = result.scalars().all()

    day_km = {i: 0.0 for i in range(7)}
    for act in activities:
        if act.completed_at:
            day_km[act.completed_at.weekday()] += act.distance_km or 0

    return ApiResponse(
        data=WeeklyData(days=[WeeklyDay(day=_DAY_NAMES[i], distance_km=round(day_km[i], 1)) for i in range(7)]),
        meta=build_meta(),
    )


@router.get("/tyre-wear", response_model=ApiResponse[TyreWearData])
async def tyre_wear(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    bikes_result = await db.execute(select(Bike).where(Bike.user_id == current_user.id))
    bikes = bikes_result.scalars().all()

    items = []
    for bike in bikes:
        tyres_result = await db.execute(select(MountedTyre).where(MountedTyre.bike_id == bike.id))
        for tyre in tyres_result.scalars().all():
            dist_result = await db.execute(
                select(func.coalesce(func.sum(Activity.distance_km), 0)).where(
                    Activity.bike_id == bike.id,
                    Activity.status == "completed",
                    Activity.started_at >= datetime(
                        tyre.mounted_at.year, tyre.mounted_at.month, tyre.mounted_at.day,
                        tzinfo=timezone.utc
                    ),
                )
            )
            done = float(dist_result.scalar())
            pct = round((done / tyre.estimated_lifespan_km) * 100, 1) if tyre.estimated_lifespan_km else 0.0
            status = "ok" if pct < 70 else ("monitor" if pct < 90 else "replace_soon")
            items.append(TyreWearItem(
                mounted_tyre_id=tyre.id,
                tyre_name=f"{tyre.brand} {tyre.model}",
                distance_done_km=round(done, 1),
                estimated_lifespan_km=tyre.estimated_lifespan_km,
                wear_percent=pct,
                replacement_status=status,
                **lookup_tyre_pics(tyre.model),
            ))

    return ApiResponse(data=TyreWearData(items=items), meta=build_meta())
