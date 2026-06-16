from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.models import Challenge, ChallengeParticipant, User
from app.schemas.challenges import ChallengeJoinData, ChallengeListData, ChallengeOut
from app.schemas.common import ApiResponse, build_meta

router = APIRouter(prefix="/challenges", tags=["Challenges"])


@router.get("", response_model=ApiResponse[ChallengeListData])
async def list_challenges(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    challenges_result = await db.execute(select(Challenge))
    challenges = challenges_result.scalars().all()

    joined_result = await db.execute(
        select(ChallengeParticipant.challenge_id).where(ChallengeParticipant.user_id == current_user.id)
    )
    joined_ids = {row[0] for row in joined_result.all()}

    items = [
        ChallengeOut(
            id=c.id,
            title=c.title,
            description=c.description,
            goal_type=c.goal_type,
            goal_value=c.goal_value,
            starts_at=c.starts_at,
            ends_at=c.ends_at,
            joined=c.id in joined_ids,
        )
        for c in challenges
    ]
    return ApiResponse(data=ChallengeListData(items=items), meta=build_meta(total=len(items)))


@router.post("/{challengeId}/join", response_model=ApiResponse[ChallengeJoinData], status_code=201)
async def join_challenge(
    challengeId: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    challenge_result = await db.execute(select(Challenge).where(Challenge.id == challengeId))
    if not challenge_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Challenge not found")

    existing = await db.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == challengeId,
            ChallengeParticipant.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already joined this challenge")

    participant = ChallengeParticipant(challenge_id=challengeId, user_id=current_user.id)
    db.add(participant)
    await db.commit()
    await db.refresh(participant)

    return ApiResponse(
        data=ChallengeJoinData(
            challenge_id=challengeId,
            joined=True,
            joined_at=participant.joined_at,
        ),
        meta=build_meta(),
    )
