from datetime import datetime
from typing import List

from pydantic import BaseModel


class ChallengeOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    goal_type: str
    goal_value: float
    starts_at: datetime
    ends_at: datetime
    joined: bool = False


class ChallengeListData(BaseModel):
    items: List[ChallengeOut]


class ChallengeJoinData(BaseModel):
    challenge_id: str
    joined: bool
    joined_at: datetime
