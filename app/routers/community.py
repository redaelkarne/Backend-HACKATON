from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.database import get_db
from app.models.models import Activity, Comment, Like, MountedTyre, Profile, User
from app.schemas.common import ApiResponse, build_meta
from app.schemas.community import (
    CommentCreateRequest, CommentOut, FeedData, FeedItem, FeedSummary, FeedUser, LikeData,
)

router = APIRouter(tags=["Community"])


@router.get("/feed", response_model=ApiResponse[FeedData])
async def get_feed(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(Activity)
        .where(Activity.status == "completed")
        .options(
            selectinload(Activity.user),
            selectinload(Activity.likes),
            selectinload(Activity.comments),
        )
        .order_by(Activity.completed_at.desc())
        .limit(limit)
    )
    activities = result.scalars().all()

    items = []
    for act in activities:
        tyres_result = await db.execute(
            select(MountedTyre).where(MountedTyre.bike_id == act.bike_id)
        )
        tyres = tyres_result.scalars().all()
        verified = any(t.brand.lower() == "michelin" for t in tyres)
        tyre_name = next((f"{t.brand} {t.model}" for t in tyres if t.brand.lower() == "michelin"), None)

        profile_result = await db.execute(select(Profile).where(Profile.user_id == act.user_id))
        profile = profile_result.scalar_one_or_none()
        avatar_url = profile.avatar_url if profile else None

        items.append(FeedItem(
            id=f"post_{act.id}",
            activity_id=act.id,
            user=FeedUser(
                id=act.user.id,
                display_name=f"{act.user.first_name} {act.user.last_name[0]}.",
                avatar_url=avatar_url,
            ),
            summary=FeedSummary(
                distance_km=act.distance_km,
                elevation_m=act.elevation_m,
                duration_seconds=act.duration_seconds,
                tyre_name=tyre_name,
            ),
            verified_michelin_review=verified,
            likes_count=len(act.likes),
            comments_count=len(act.comments),
            created_at=act.completed_at,
        ))

    return ApiResponse(data=FeedData(items=items), meta=build_meta(total=len(items)))


@router.post("/activities/{activityId}/like", response_model=ApiResponse[LikeData], status_code=201)
async def like_activity(
    activityId: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    act_result = await db.execute(select(Activity).where(Activity.id == activityId))
    if not act_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Activity not found")

    like_result = await db.execute(
        select(Like).where(Like.activity_id == activityId, Like.user_id == current_user.id)
    )
    existing_like = like_result.scalar_one_or_none()

    if existing_like:
        await db.delete(existing_like)
        liked = False
    else:
        db.add(Like(user_id=current_user.id, activity_id=activityId))
        liked = True

    await db.commit()

    count_result = await db.execute(
        select(Like).where(Like.activity_id == activityId)
    )
    likes_count = len(count_result.scalars().all())

    return ApiResponse(
        data=LikeData(activity_id=activityId, liked=liked, likes_count=likes_count),
        meta=build_meta(),
    )


@router.post("/activities/{activityId}/comments", response_model=ApiResponse[CommentOut], status_code=201)
async def add_comment(
    activityId: str,
    body: CommentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    act_result = await db.execute(select(Activity).where(Activity.id == activityId))
    if not act_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Activity not found")

    comment = Comment(activity_id=activityId, user_id=current_user.id, content=body.content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return ApiResponse(data=CommentOut.model_validate(comment), meta=build_meta())
