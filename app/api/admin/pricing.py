from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.models.entities import ModelPricing
from app.schemas.admin import ModelPricingOut, ModelPricingUpsert

router = APIRouter(prefix="/admin/pricing", tags=["admin-pricing"])


@router.put("", response_model=ModelPricingOut)
async def upsert_model_pricing(
    payload: ModelPricingUpsert,
    session: AsyncSession = Depends(get_db_session),
) -> ModelPricing:
    pricing = (
        await session.execute(select(ModelPricing).where(ModelPricing.public_model == payload.public_model))
    ).scalars().first()

    if pricing is None:
        pricing = ModelPricing(**payload.model_dump(), currency=settings.default_currency)
        session.add(pricing)
    else:
        for k, v in payload.model_dump().items():
            setattr(pricing, k, v)
        pricing.currency = settings.default_currency

    await session.commit()
    await session.refresh(pricing)
    return pricing


@router.get("", response_model=list[ModelPricingOut])
async def list_model_pricing(session: AsyncSession = Depends(get_db_session)) -> list[ModelPricing]:
    return list((await session.execute(select(ModelPricing).order_by(ModelPricing.public_model.asc()))).scalars().all())


@router.delete("/{public_model}")
async def delete_model_pricing(
    public_model: str = Path(..., min_length=1),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    pricing = (await session.execute(select(ModelPricing).where(ModelPricing.public_model == public_model))).scalars().first()
    if pricing is None:
        raise HTTPException(status_code=404, detail="pricing not found")

    await session.delete(pricing)
    await session.commit()
    return {"ok": True}


@router.delete("/id/{pricing_id}")
async def delete_model_pricing_by_id(
    pricing_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    pricing = (await session.execute(select(ModelPricing).where(ModelPricing.id == pricing_id))).scalars().first()
    if pricing is None:
        raise HTTPException(status_code=404, detail="pricing not found")

    await session.delete(pricing)
    await session.commit()
    return {"ok": True}


@router.delete("")
async def delete_model_pricing_compat(
    public_model: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    if not public_model or not public_model.strip():
        raise HTTPException(status_code=400, detail="public_model is required")

    pricing = (await session.execute(select(ModelPricing).where(ModelPricing.public_model == public_model))).scalars().first()
    if pricing is None:
        raise HTTPException(status_code=404, detail="pricing not found")

    await session.delete(pricing)
    await session.commit()
    return {"ok": True}


@router.delete("/")
async def delete_model_pricing_compat_slash(
    public_model: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    return await delete_model_pricing_compat(public_model=public_model, session=session)
