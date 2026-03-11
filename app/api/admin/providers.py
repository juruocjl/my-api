from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.entities import ApiKey, ModelRoute, Provider
from app.schemas.admin import (
    ApiKeyCreate,
    ApiKeyOut,
    ApiKeyUpdate,
    ModelRouteCreate,
    ModelRouteOut,
    ModelRouteUpdate,
    ProviderCreate,
    ProviderOut,
    ProviderUpdate,
)

router = APIRouter(prefix="/admin/providers", tags=["admin-providers"])


def _to_api_key_out(key: ApiKey) -> ApiKeyOut:
    return ApiKeyOut(
        id=key.id,
        provider_id=key.provider_id,
        key_name=key.key_name,
        enabled=key.enabled,
        balance=key.balance,
        weight=key.weight,
        consecutive_failures=key.consecutive_failures,
        cooldown_until=key.cooldown_until.isoformat() if key.cooldown_until else None,
        last_error=key.last_error,
    )


@router.post("", response_model=ProviderOut)
async def create_provider(payload: ProviderCreate, session: AsyncSession = Depends(get_db_session)) -> Provider:
    existing = (await session.execute(select(Provider).where(Provider.name == payload.name))).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="provider name already exists")

    provider = Provider(**payload.model_dump())
    session.add(provider)
    await session.commit()
    await session.refresh(provider)
    return provider


@router.get("", response_model=list[ProviderOut])
async def list_providers(session: AsyncSession = Depends(get_db_session)) -> list[Provider]:
    return list((await session.execute(select(Provider).order_by(Provider.id.asc()))).scalars().all())


@router.patch("/{provider_id}", response_model=ProviderOut)
async def update_provider(
    payload: ProviderUpdate,
    provider_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_db_session),
) -> Provider:
    provider = (await session.execute(select(Provider).where(Provider.id == provider_id))).scalars().first()
    if provider is None:
        raise HTTPException(status_code=404, detail="provider not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(provider, k, v)

    await session.commit()
    await session.refresh(provider)
    return provider


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    provider = (await session.execute(select(Provider).where(Provider.id == provider_id))).scalars().first()
    if provider is None:
        raise HTTPException(status_code=404, detail="provider not found")

    await session.delete(provider)
    await session.commit()
    return {"ok": True}


@router.post("/{provider_id}/keys", response_model=ApiKeyOut)
async def add_provider_key(
    payload: ApiKeyCreate,
    provider_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_db_session),
) -> ApiKeyOut:
    provider = (await session.execute(select(Provider).where(Provider.id == provider_id))).scalars().first()
    if provider is None:
        raise HTTPException(status_code=404, detail="provider not found")

    key = ApiKey(provider_id=provider_id, **payload.model_dump())
    session.add(key)
    await session.commit()
    await session.refresh(key)

    return _to_api_key_out(key)


@router.get("/keys", response_model=list[ApiKeyOut])
async def list_all_keys(session: AsyncSession = Depends(get_db_session)) -> list[ApiKeyOut]:
    keys = list((await session.execute(select(ApiKey).order_by(ApiKey.weight.desc(), ApiKey.id.asc()))).scalars().all())
    return [_to_api_key_out(item) for item in keys]


@router.get("/{provider_id}/keys", response_model=list[ApiKeyOut])
async def list_provider_keys(
    provider_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_db_session),
) -> list[ApiKeyOut]:
    keys = list(
        (
            await session.execute(
                select(ApiKey)
                .where(ApiKey.provider_id == provider_id)
                .order_by(ApiKey.weight.desc(), ApiKey.id.asc())
            )
        )
        .scalars()
        .all()
    )
    return [_to_api_key_out(item) for item in keys]


@router.patch("/keys/{key_id}", response_model=ApiKeyOut)
async def update_provider_key(
    payload: ApiKeyUpdate,
    key_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_db_session),
) -> ApiKeyOut:
    key = (await session.execute(select(ApiKey).where(ApiKey.id == key_id))).scalars().first()
    if key is None:
        raise HTTPException(status_code=404, detail="api key not found")

    data = payload.model_dump(exclude_unset=True)
    balance_delta = data.pop("balance_delta", None)
    for k, v in data.items():
        setattr(key, k, v)

    if balance_delta is not None:
        key.balance = (key.balance or 0.0) + balance_delta

    await session.commit()
    await session.refresh(key)

    return _to_api_key_out(key)


@router.delete("/keys/{key_id}")
async def delete_provider_key(
    key_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    key = (await session.execute(select(ApiKey).where(ApiKey.id == key_id))).scalars().first()
    if key is None:
        raise HTTPException(status_code=404, detail="api key not found")

    await session.delete(key)
    await session.commit()
    return {"ok": True}


@router.post("/routes", response_model=ModelRouteOut)
async def create_model_route(
    payload: ModelRouteCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ModelRoute:
    provider = (await session.execute(select(Provider).where(Provider.id == payload.provider_id))).scalars().first()
    if provider is None:
        raise HTTPException(status_code=404, detail="provider not found")

    route = ModelRoute(**payload.model_dump())
    session.add(route)
    await session.commit()
    await session.refresh(route)
    return route


@router.get("/routes", response_model=list[ModelRouteOut])
async def list_model_routes(session: AsyncSession = Depends(get_db_session)) -> list[ModelRoute]:
    return list((await session.execute(select(ModelRoute).order_by(ModelRoute.id.asc()))).scalars().all())


@router.patch("/routes/{route_id}", response_model=ModelRouteOut)
async def update_model_route(
    payload: ModelRouteUpdate,
    route_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_db_session),
) -> ModelRoute:
    route = (await session.execute(select(ModelRoute).where(ModelRoute.id == route_id))).scalars().first()
    if route is None:
        raise HTTPException(status_code=404, detail="route not found")

    data = payload.model_dump(exclude_unset=True)
    if "provider_id" in data:
        provider = (await session.execute(select(Provider).where(Provider.id == data["provider_id"]))).scalars().first()
        if provider is None:
            raise HTTPException(status_code=404, detail="provider not found")

    for k, v in data.items():
        setattr(route, k, v)

    await session.commit()
    await session.refresh(route)
    return route


@router.delete("/routes/{route_id}")
async def delete_model_route(
    route_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    route = (await session.execute(select(ModelRoute).where(ModelRoute.id == route_id))).scalars().first()
    if route is None:
        raise HTTPException(status_code=404, detail="route not found")

    await session.delete(route)
    await session.commit()
    return {"ok": True}
