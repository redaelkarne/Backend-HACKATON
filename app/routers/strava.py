"""
Strava integration — OAuth2 connect + activity import.

Flow:
  1. GET  /strava/connect        → authenticated user gets an OAuth URL to open in browser
  2. User authorises on Strava → Strava redirects to GET /strava/callback?code=...&state={user_id}
  3. GET  /strava/activities      → list the user's recent Strava activities with their strava_id
  4. POST /strava/import          → import one activity (by strava_id) as a local Activity with GPS route
"""
import json
import time
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import get_current_user
from app.database import get_db
from app.models.models import Activity, Bike, User
from app.schemas.activities import ActivityOut
from app.schemas.common import ApiResponse, build_meta
from app.schemas.strava import (
    StravaActivityPreview,
    StravaConnectedOut,
    StravaConnectOut,
    StravaImportRequest,
)

router = APIRouter(prefix="/strava", tags=["Strava"])

_STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
_STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
_STRAVA_API = "https://www.strava.com/api/v3"


# ── helpers ──────────────────────────────────────────────────────────────────

def _oauth_configured() -> None:
    """Required only for the OAuth endpoints (connect + callback)."""
    if not settings.strava_client_id or not settings.strava_client_secret:
        raise HTTPException(
            status_code=503,
            detail="Strava OAuth not configured. Set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in .env",
        )


def _require_connected(user: User) -> None:
    if not user.strava_access_token:
        raise HTTPException(
            status_code=400,
            detail="Strava account not connected. Call GET /strava/connect first.",
        )


async def _valid_token(user: User, db: AsyncSession) -> str:
    """Return a valid access token, refreshing it if it has expired."""
    if user.strava_token_expires_at and user.strava_token_expires_at > int(time.time()) + 60:
        return user.strava_access_token

    async with httpx.AsyncClient() as client:
        r = await client.post(_STRAVA_TOKEN_URL, json={
            "client_id": settings.strava_client_id,
            "client_secret": settings.strava_client_secret,
            "refresh_token": user.strava_refresh_token,
            "grant_type": "refresh_token",
        })
        if r.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Strava token refresh failed — please reconnect via GET /strava/connect",
            )
        data = r.json()

    user.strava_access_token = data["access_token"]
    user.strava_refresh_token = data["refresh_token"]
    user.strava_token_expires_at = data["expires_at"]
    db.add(user)
    await db.commit()
    return user.strava_access_token


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/connect",
    response_model=ApiResponse[StravaConnectOut],
    summary="Step 1 — Get the Strava OAuth URL",
    description=(
        "Returns a URL to open in the user's browser (or a WebView in mobile). "
        "The user authorises the app on Strava, then Strava redirects to `GET /strava/callback`. "
        "Requires the user to be logged in (JWT) so we know which account to link."
    ),
)
async def connect_strava(current_user: User = Depends(get_current_user)):
    _oauth_configured()
    params = "&".join([
        f"client_id={settings.strava_client_id}",
        f"redirect_uri={settings.strava_redirect_uri}",
        "response_type=code",
        "scope=activity:read_all",
        f"state={current_user.id}",
        "approval_prompt=auto",
    ])
    url = f"{_STRAVA_AUTH_URL}?{params}"
    return ApiResponse(
        data=StravaConnectOut(
            auth_url=url,
            message="Open this URL in a browser to connect your Strava account.",
        ),
        meta=build_meta(),
    )


@router.get(
    "/callback",
    response_model=ApiResponse[StravaConnectedOut],
    summary="Step 2 — OAuth callback (Strava redirects here)",
    description=(
        "Strava calls this endpoint with `?code=...&state={user_id}` after the user authorises. "
        "**Do not call this manually** — it is triggered automatically by the Strava redirect. "
        "Exchanges the code for tokens and stores them on the user record."
    ),
)
async def strava_callback(
    code: str = Query(..., description="Authorization code provided by Strava"),
    state: str = Query(..., description="user_id passed through the OAuth state param"),
    scope: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    _oauth_configured()

    async with httpx.AsyncClient() as client:
        r = await client.post(_STRAVA_TOKEN_URL, json={
            "client_id": settings.strava_client_id,
            "client_secret": settings.strava_client_secret,
            "code": code,
            "grant_type": "authorization_code",
        })
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Strava authorization failed: {r.text}")
        data = r.json()

    result = await db.execute(select(User).where(User.id == state))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    athlete = data.get("athlete", {})
    user.strava_athlete_id = str(athlete.get("id", ""))
    user.strava_access_token = data["access_token"]
    user.strava_refresh_token = data["refresh_token"]
    user.strava_token_expires_at = data["expires_at"]
    db.add(user)
    await db.commit()

    return ApiResponse(
        data=StravaConnectedOut(
            connected=True,
            athlete_id=user.strava_athlete_id,
            athlete_name=f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip(),
        ),
        meta=build_meta(),
    )


@router.get(
    "/activities",
    response_model=ApiResponse[List[StravaActivityPreview]],
    summary="Step 3 — List recent Strava activities",
    description=(
        "Returns the user's recent activities from Strava, including their `strava_id`. "
        "Use the `strava_id` to import a specific activity via `POST /strava/import`."
    ),
)
async def list_strava_activities(
    per_page: int = Query(default=20, le=50, description="Number of activities to return (max 50)"),
    page: int = Query(default=1, ge=1, description="Page number for pagination"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_connected(current_user)
    token = await _valid_token(current_user, db)

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_STRAVA_API}/athlete/activities",
            params={"per_page": per_page, "page": page},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch activities from Strava")
        activities = r.json()

    previews = [
        StravaActivityPreview(
            strava_id=a["id"],
            name=a.get("name", "Strava Activity"),
            sport_type=a.get("sport_type") or a.get("type", "Ride"),
            distance_km=round(a.get("distance", 0) / 1000, 2),
            duration_seconds=a.get("moving_time", 0),
            elevation_m=round(a.get("total_elevation_gain", 0), 1),
            started_at=datetime.fromisoformat(a["start_date"].replace("Z", "+00:00")),
        )
        for a in activities
    ]
    return ApiResponse(data=previews, meta=build_meta(total=len(previews)))


@router.post(
    "/import",
    response_model=ApiResponse[ActivityOut],
    status_code=201,
    summary="Step 4 — Import a Strava activity",
    description=(
        "Fetches the full activity data and GPS route from Strava and saves it as a local Activity. "
        "The GPS coordinates are stored in the same format as GPX imports, "
        "so `GET /activities/{id}/route` works identically for both."
    ),
)
async def import_strava_activity(
    body: StravaImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_connected(current_user)
    token = await _valid_token(current_user, db)

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Fetch activity details
        act_r = await client.get(
            f"{_STRAVA_API}/activities/{body.strava_activity_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if act_r.status_code == 404:
            raise HTTPException(status_code=404, detail="Strava activity not found")
        if act_r.status_code == 401:
            raise HTTPException(status_code=401, detail="Strava token invalid — reconnect via GET /strava/connect")
        if act_r.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch activity from Strava")
        act = act_r.json()

        # Fetch GPS streams (latlng + altitude)
        streams_r = await client.get(
            f"{_STRAVA_API}/activities/{body.strava_activity_id}/streams",
            params={"keys": "latlng", "key_by_type": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        latlng = []
        if streams_r.status_code == 200:
            latlng = streams_r.json().get("latlng", {}).get("data", [])

    # Sample every 10th point — same strategy as GPX import
    sampled = latlng[::10] if len(latlng) > 10 else latlng
    route_polyline = json.dumps(sampled) if sampled else None

    # Resolve bike
    bike_id = body.bike_id
    if not bike_id:
        bike_result = await db.execute(
            select(Bike).where(Bike.user_id == current_user.id).limit(1)
        )
        bike = bike_result.scalar_one_or_none()
        if not bike:
            raise HTTPException(
                status_code=400,
                detail="No bike on your profile. Add one first via POST /profiles/{userId}/bike.",
            )
        bike_id = bike.id

    def _parse_strava_dt(s: str) -> datetime:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))

    started_at = _parse_strava_dt(act["start_date"])
    elapsed = act.get("elapsed_time") or act.get("moving_time") or 0
    completed_at = datetime.fromtimestamp(started_at.timestamp() + elapsed, tz=timezone.utc)

    activity = Activity(
        user_id=current_user.id,
        bike_id=bike_id,
        type=body.type,
        status="completed",
        weather=body.weather,
        notes=act.get("name"),
        distance_km=round(act.get("distance", 0) / 1000, 2),
        duration_seconds=act.get("moving_time", 0),
        elevation_m=round(act.get("total_elevation_gain", 0), 1),
        average_speed_kmh=round((act.get("average_speed") or 0) * 3.6, 1),
        route_polyline=route_polyline,
        started_at=started_at,
        completed_at=completed_at,
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return ApiResponse(data=ActivityOut.model_validate(activity), meta=build_meta())
