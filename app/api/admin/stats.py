from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.entities import ApiKey, DailyUsageSummary, UsageEvent
from app.schemas.stats import (
    DailyUsageItem,
    DailyUsageResponse,
    DailyUsageTotals,
    RemainingQuotaResponse,
    TotalCostResponse,
    UsageEventItem,
    UsageEventResponse,
)

router = APIRouter(prefix="/admin/stats", tags=["admin-stats"])


@router.get("/daily", response_model=DailyUsageResponse)
async def get_daily_stats(
    start_date: date = Query(...),
    end_date: date = Query(...),
    model: str | None = Query(default=None),
    provider_id: int | None = Query(default=None),
    key_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> DailyUsageResponse:
    conds = [DailyUsageSummary.usage_date >= start_date, DailyUsageSummary.usage_date <= end_date]
    if model:
        conds.append(DailyUsageSummary.public_model == model)
    if provider_id is not None:
        conds.append(DailyUsageSummary.provider_id == provider_id)
    if key_id is not None:
        conds.append(DailyUsageSummary.api_key_id == key_id)

    stmt = select(DailyUsageSummary).where(and_(*conds)).order_by(DailyUsageSummary.usage_date.asc())
    rows = list((await session.execute(stmt)).scalars().all())

    items = [
        DailyUsageItem(
            usage_date=r.usage_date,
            public_model=r.public_model,
            provider_id=r.provider_id,
            api_key_id=r.api_key_id,
            input_tokens=r.input_tokens,
            cached_input_tokens=r.cached_input_tokens,
            output_tokens=r.output_tokens,
            total_cost=r.total_cost,
            request_count=r.request_count,
            estimated_count=r.estimated_count,
        )
        for r in rows
    ]

    totals = DailyUsageTotals(
        input_tokens=sum(i.input_tokens for i in items),
        cached_input_tokens=sum(i.cached_input_tokens for i in items),
        output_tokens=sum(i.output_tokens for i in items),
        total_cost=sum(i.total_cost for i in items),
        request_count=sum(i.request_count for i in items),
        estimated_count=sum(i.estimated_count for i in items),
    )

    return DailyUsageResponse(items=items, totals=totals)


@router.get("/events", response_model=UsageEventResponse)
async def get_usage_events(
    start_date: date = Query(...),
    end_date: date = Query(...),
    model: str | None = Query(default=None),
    provider_id: int | None = Query(default=None),
    key_id: int | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    session: AsyncSession = Depends(get_db_session),
) -> UsageEventResponse:
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)

    conds = [UsageEvent.created_at >= start_dt, UsageEvent.created_at <= end_dt]
    if model:
        conds.append(UsageEvent.public_model == model)
    if provider_id is not None:
        conds.append(UsageEvent.provider_id == provider_id)
    if key_id is not None:
        conds.append(UsageEvent.api_key_id == key_id)

    stmt = (
        select(UsageEvent)
        .where(and_(*conds))
        .order_by(UsageEvent.created_at.desc())
        .limit(limit)
    )
    rows = list((await session.execute(stmt)).scalars().all())

    items = [
        UsageEventItem(
            request_id=r.request_id,
            created_at=r.created_at,
            endpoint=r.endpoint,
            public_model=r.public_model,
            provider_id=r.provider_id,
            api_key_id=r.api_key_id,
            input_tokens=r.input_tokens,
            cached_input_tokens=r.cached_input_tokens,
            output_tokens=r.output_tokens,
            total_cost=r.total_cost,
            is_estimated=r.is_estimated,
            latency_ms=r.latency_ms,
        )
        for r in rows
    ]

    return UsageEventResponse(items=items)


@router.get("/total-cost", response_model=TotalCostResponse)
async def get_total_cost(
    start_date: date = Query(...),
    end_date: date = Query(...),
    model: str | None = Query(default=None),
    provider_id: int | None = Query(default=None),
    key_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> TotalCostResponse:
    conds = [DailyUsageSummary.usage_date >= start_date, DailyUsageSummary.usage_date <= end_date]
    if model:
        conds.append(DailyUsageSummary.public_model == model)
    if provider_id is not None:
        conds.append(DailyUsageSummary.provider_id == provider_id)
    if key_id is not None:
        conds.append(DailyUsageSummary.api_key_id == key_id)

    stmt = select(DailyUsageSummary.total_cost).where(and_(*conds))
    costs = (await session.execute(stmt)).scalars().all()
    total_cost = float(sum(costs))

    return TotalCostResponse(start_date=start_date, end_date=end_date, total_cost=total_cost)


@router.get("/remaining-quota", response_model=RemainingQuotaResponse)
async def get_remaining_quota(session: AsyncSession = Depends(get_db_session)) -> RemainingQuotaResponse:
    keys = list((await session.execute(select(ApiKey))).scalars().all())
    balances = [float(k.balance or 0.0) for k in keys]

    total_balance = float(sum(balances))
    positive_balance = float(sum(v for v in balances if v > 0))
    enabled_key_count = sum(1 for k in keys if k.enabled)

    return RemainingQuotaResponse(
        total_balance=total_balance,
        positive_balance=positive_balance,
        enabled_key_count=enabled_key_count,
        total_key_count=len(keys),
    )
