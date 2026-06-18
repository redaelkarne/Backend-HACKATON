from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.catalogue import lookup_tyre_db, lookup_tyre_pics
from app.core.security import get_current_user
from app.database import get_db
from app.models.models import Activity, Bike, MountedTyre, Profile, User
from app.schemas.common import ApiResponse, build_meta
from app.schemas.profiles import (
    BikeCreateRequest, BikesListData, BikeOut, BikeWithTyresOut, MountedTyreCreateRequest,
    MountedTyreOut, Preferences, ProfileOut, ProfileStats, ProfileUpdateRequest,
)

router = APIRouter(prefix="/profiles", tags=["Profile"])


async def _get_profile_out(user_id: str, db: AsyncSession) -> ProfileOut:
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_km_result = await db.execute(
        select(func.coalesce(func.sum(Activity.distance_km), 0))
        .where(Activity.user_id == user_id, Activity.status == "completed")
    )
    total_rides_result = await db.execute(
        select(func.count(Activity.id))
        .where(Activity.user_id == user_id, Activity.status == "completed")
    )
    total_km = float(total_km_result.scalar())
    total_rides = int(total_rides_result.scalar())

    prefs = None
    if profile and profile.preferences:
        prefs = Preferences(**profile.preferences)

    return ProfileOut(
        user_id=user_id,
        avatar_url=profile.avatar_url if profile else None,
        rider_type=profile.rider_type if profile else "route",
        bio=profile.bio if profile else None,
        preferences=prefs,
        stats=ProfileStats(total_km=total_km, total_rides=total_rides, level=user.level),
    )


@router.get("/{userId}", response_model=ApiResponse[ProfileOut])
async def get_profile(userId: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return ApiResponse(data=await _get_profile_out(userId, db), meta=build_meta())


@router.patch("/{userId}", response_model=ApiResponse[ProfileOut])
async def update_profile(
    userId: str,
    body: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Profile).where(Profile.user_id == userId))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if body.avatar_url is not None:
        profile.avatar_url = body.avatar_url
    if body.rider_type is not None:
        profile.rider_type = body.rider_type
    if body.bio is not None:
        profile.bio = body.bio
    if body.preferences is not None:
        profile.preferences = body.preferences.model_dump()

    await db.commit()
    return ApiResponse(data=await _get_profile_out(userId, db), meta=build_meta())


@router.get("/{userId}/bikes", response_model=ApiResponse[BikesListData])
async def list_bikes(userId: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(
        select(Bike).where(Bike.user_id == userId).options(selectinload(Bike.mounted_tyres))
    )
    bikes = result.scalars().all()

    items = []
    for bike in bikes:
        tyres_out = []
        for tyre in bike.mounted_tyres:
            tyre_info = await lookup_tyre_db(tyre.model, db)
            tyres_out.append(MountedTyreOut(
                id=tyre.id,
                bike_id=tyre.bike_id,
                brand=tyre.brand,
                model=tyre.model,
                size=tyre.size,
                mounted_at=str(tyre.mounted_at),
                estimated_lifespan_km=tyre.estimated_lifespan_km,
                **tyre_info,
            ))
        items.append(BikeWithTyresOut(
            id=bike.id,
            user_id=bike.user_id,
            brand=bike.brand,
            model=bike.model,
            category=bike.category,
            wheel_size=bike.wheel_size,
            mounted_tyres=tyres_out,
        ))
    return ApiResponse(data=BikesListData(items=items), meta=build_meta(total=len(items)))


@router.post("/{userId}/bike", response_model=ApiResponse[BikeOut], status_code=201)
async def add_bike(
    userId: str,
    body: BikeCreateRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    bike = Bike(user_id=userId, **body.model_dump())
    db.add(bike)
    await db.commit()
    await db.refresh(bike)
    return ApiResponse(data=BikeOut.model_validate(bike), meta=build_meta())


@router.post("/{userId}/mounted-tyres", response_model=ApiResponse[MountedTyreOut], status_code=201)
async def add_mounted_tyre(
    userId: str,
    body: MountedTyreCreateRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    tyre = MountedTyre(**body.model_dump())
    db.add(tyre)
    await db.commit()
    await db.refresh(tyre)
    data = MountedTyreOut(
        id=tyre.id,
        bike_id=tyre.bike_id,
        brand=tyre.brand,
        model=tyre.model,
        size=tyre.size,
        mounted_at=str(tyre.mounted_at),
        estimated_lifespan_km=tyre.estimated_lifespan_km,
        **lookup_tyre_pics(tyre.model),
    )
    return ApiResponse(data=data, meta=build_meta())
