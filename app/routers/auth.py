from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models.models import Profile, User
from app.schemas.auth import AuthPayload, LoginRequest, RegisterRequest, UserOut
from app.schemas.common import ApiResponse, build_meta

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=ApiResponse[AuthPayload], status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already exists")

    user = User(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.flush()

    profile = Profile(user_id=user.id, rider_type="route")
    db.add(profile)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    return ApiResponse(
        data=AuthPayload(user=UserOut.model_validate(user), access_token=token),
        meta=build_meta(),
    )


@router.post("/login", response_model=ApiResponse[AuthPayload])
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return ApiResponse(
        data=AuthPayload(user=UserOut.model_validate(user), access_token=token),
        meta=build_meta(),
    )


@router.get("/me", response_model=ApiResponse[UserOut])
async def me(current_user: User = Depends(get_current_user)):
    return ApiResponse(data=UserOut.model_validate(current_user), meta=build_meta())
