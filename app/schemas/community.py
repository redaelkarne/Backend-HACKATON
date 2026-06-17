from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class FeedUser(BaseModel):
    id: str
    display_name: str
    avatar_url: Optional[str] = None


class FeedSummary(BaseModel):
    distance_km: Optional[float] = None
    elevation_m: Optional[float] = None
    duration_seconds: Optional[int] = None
    tyre_name: Optional[str] = None
    tyre_catalogue_id: Optional[int] = None


class FeedItem(BaseModel):
    id: str
    activity_id: str
    user: FeedUser
    summary: FeedSummary
    verified_michelin_review: bool
    likes_count: int
    comments_count: int
    created_at: datetime


class FeedData(BaseModel):
    items: List[FeedItem]


class LikeData(BaseModel):
    activity_id: str
    liked: bool
    likes_count: int


class CommentCreateRequest(BaseModel):
    content: str


class CommentOut(BaseModel):
    id: str
    activity_id: str
    user_id: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentWithUser(BaseModel):
    id: str
    activity_id: str
    user_id: str
    display_name: str
    avatar_url: Optional[str] = None
    content: str
    created_at: datetime


class CommentListData(BaseModel):
    items: List[CommentWithUser]


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    display_name: str
    avatar_url: Optional[str] = None
    distance_km: float


class LeaderboardData(BaseModel):
    items: List[LeaderboardEntry]
