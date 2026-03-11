from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.entities import DailyUsageSummary
from app.schemas.stats import DailyUsageItem, DailyUsageResponse, DailyUsageTotals

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
