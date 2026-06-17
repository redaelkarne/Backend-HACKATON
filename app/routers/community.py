from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.catalogue import lookup_tyre_db
from app.core.security import get_current_user
from app.database import get_db
from app.models.models import Activity, Comment, Like, MountedTyre, Profile, User
from app.schemas.common import ApiResponse, build_meta
from app.schemas.community import (
    CommentCreateRequest, CommentListData, CommentOut, CommentWithUser, FeedData, FeedItem,
    FeedSummary, FeedUser, LeaderboardData, LeaderboardEntry, LikeData,
)

router = APIRouter(tags=["Community"])


@router.get("/leaderboard", response_model=ApiResponse[LeaderboardData])
async def get_leaderboard(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(Activity.user_id, func.sum(Activity.distance_km).label("total_km"))
        .where(Activity.status == "completed", Activity.completed_at >= week_start)
        .group_by(Activity.user_id)
        .order_by(func.sum(Activity.distance_km).desc())
        .limit(limit)
    )
    rows = result.all()

    items = []
    for rank, (user_id, total_km) in enumerate(rows, start=1):
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            continue
        profile_result = await db.execute(select(Profile).where(Profile.user_id == user_id))
        profile = profile_result.scalar_one_or_none()
        items.append(LeaderboardEntry(
            rank=rank,
            user_id=user_id,
            display_name=f"{user.first_name} {user.last_name[0]}.",
            avatar_url=profile.avatar_url if profile else None,
            distance_km=round(float(total_km or 0), 1),
        ))

    return ApiResponse(data=LeaderboardData(items=items), meta=build_meta(total=len(items)))


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
        michelin_tyre = next((t for t in tyres if t.brand.lower() == "michelin"), None)
        tyre_name = f"{michelin_tyre.brand} {michelin_tyre.model}" if michelin_tyre else None

        tyre_info = await lookup_tyre_db(michelin_tyre.model, db) if michelin_tyre else {}

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
                tyre_catalogue_id=tyre_info.get("catalogue_id"),
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


@router.get("/activities/{activityId}/comments", response_model=ApiResponse[CommentListData])
async def list_comments(
    activityId: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(Comment)
        .where(Comment.activity_id == activityId)
        .options(selectinload(Comment.user))
        .order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()

    items = []
    for comment in comments:
        profile_result = await db.execute(select(Profile).where(Profile.user_id == comment.user_id))
        profile = profile_result.scalar_one_or_none()
        items.append(CommentWithUser(
            id=comment.id,
            activity_id=comment.activity_id,
            user_id=comment.user_id,
            display_name=f"{comment.user.first_name} {comment.user.last_name[0]}.",
            avatar_url=profile.avatar_url if profile else None,
            content=comment.content,
            created_at=comment.created_at,
        ))

    return ApiResponse(data=CommentListData(items=items), meta=build_meta(total=len(items)))
