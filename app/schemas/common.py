import uuid
from datetime import datetime, timezone
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    request_id: str
    timestamp: datetime
    total: Optional[int] = None


class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: Meta


def build_meta(total: Optional[int] = None) -> Meta:
    return Meta(
        request_id=f"req_{uuid.uuid4().hex[:8]}",
        timestamp=datetime.now(timezone.utc),
        total=total,
    )
