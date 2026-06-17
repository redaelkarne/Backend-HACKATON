from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Tyre
from app.schemas.catalogue import TyreListData, TyreOut
from app.schemas.common import ApiResponse, build_meta

router = APIRouter(prefix="/catalogue", tags=["Catalogue"])


@router.get("", response_model=ApiResponse[TyreListData])
async def list_tyres(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tyre))
    tyres = result.scalars().all()
    items = [TyreOut.model_validate(t) for t in tyres]
    return ApiResponse(data=TyreListData(items=items), meta=build_meta(total=len(items)))


@router.get("/{tyre_id}", response_model=ApiResponse[TyreOut])
async def get_tyre(tyre_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tyre).where(Tyre.id == tyre_id))
    tyre = result.scalar_one_or_none()
    if not tyre:
        raise HTTPException(status_code=404, detail="Tyre not found")
    return ApiResponse(data=TyreOut.model_validate(tyre), meta=build_meta())
