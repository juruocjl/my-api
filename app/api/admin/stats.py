from collections import defaultdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.timezone import local_date_range_to_utc_naive, local_datetime_to_utc_naive, utc_naive_to_business
from app.models.entities import ApiKey, UsageEvent
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
    start_dt, end_dt = local_date_range_to_utc_naive(start_date, end_date)
    conds = [UsageEvent.created_at >= start_dt, UsageEvent.created_at <= end_dt]
    if model:
        conds.append(UsageEvent.public_model == model)
    if provider_id is not None:
        conds.append(UsageEvent.provider_id == provider_id)
    if key_id is not None:
        conds.append(UsageEvent.api_key_id == key_id)

    stmt = select(UsageEvent).where(and_(*conds)).order_by(UsageEvent.created_at.asc())
    rows = list((await session.execute(stmt)).scalars().all())

    grouped: dict[tuple[date, str, int, int], dict[str, int | float | date | str]] = defaultdict(
        lambda: {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "total_cost": 0.0,
            "request_count": 0,
            "estimated_count": 0,
        }
    )

    for row in rows:
        business_date = utc_naive_to_business(row.created_at).date()
        group_key = (business_date, row.public_model, row.provider_id, row.api_key_id)
        bucket = grouped[group_key]
        bucket["input_tokens"] += row.input_tokens
        bucket["cached_input_tokens"] += row.cached_input_tokens
        bucket["output_tokens"] += row.output_tokens
        bucket["total_cost"] += row.total_cost
        bucket["request_count"] += 1
        bucket["estimated_count"] += 1 if row.is_estimated else 0

    items = [
        DailyUsageItem(
            usage_date=usage_date,
            public_model=public_model,
            provider_id=provider_id_value,
            api_key_id=key_id_value,
            input_tokens=int(bucket["input_tokens"]),
            cached_input_tokens=int(bucket["cached_input_tokens"]),
            output_tokens=int(bucket["output_tokens"]),
            total_cost=float(bucket["total_cost"]),
            request_count=int(bucket["request_count"]),
            estimated_count=int(bucket["estimated_count"]),
        )
        for (usage_date, public_model, provider_id_value, key_id_value), bucket in sorted(grouped.items())
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
    start_dt, end_dt = local_date_range_to_utc_naive(start_date, end_date)

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
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    model: str | None = Query(default=None),
    provider_id: int | None = Query(default=None),
    key_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> TotalCostResponse:
    using_datetime = start_time is not None or end_time is not None

    if using_datetime:
        if start_time is None or end_time is None:
            raise HTTPException(status_code=422, detail="start_time 和 end_time 需要同时提供")
        start_dt = local_datetime_to_utc_naive(start_time)
        end_dt = local_datetime_to_utc_naive(end_time)
        conds = [UsageEvent.created_at >= start_dt, UsageEvent.created_at <= end_dt]
        if model:
            conds.append(UsageEvent.public_model == model)
        if provider_id is not None:
            conds.append(UsageEvent.provider_id == provider_id)
        if key_id is not None:
            conds.append(UsageEvent.api_key_id == key_id)

        stmt = select(UsageEvent.total_cost).where(and_(*conds))
        costs = (await session.execute(stmt)).scalars().all()
        total_cost = float(sum(costs))
        return TotalCostResponse(start_time=start_time, end_time=end_time, total_cost=total_cost)

    if start_date is None or end_date is None:
        raise HTTPException(status_code=422, detail="请提供 start_date/end_date，或 start_time/end_time")

    start_dt, end_dt = local_date_range_to_utc_naive(start_date, end_date)
    conds = [UsageEvent.created_at >= start_dt, UsageEvent.created_at <= end_dt]
    if model:
        conds.append(UsageEvent.public_model == model)
    if provider_id is not None:
        conds.append(UsageEvent.provider_id == provider_id)
    if key_id is not None:
        conds.append(UsageEvent.api_key_id == key_id)

    stmt = select(UsageEvent.total_cost).where(and_(*conds))
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
