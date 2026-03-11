from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.billing import PricingConfig, TokenUsage, calculate_cost
from app.models.entities import ApiKey, DailyUsageSummary, ModelPricing, UsageEvent


async def get_model_pricing(session: AsyncSession, public_model: str) -> ModelPricing | None:
    stmt = select(ModelPricing).where(ModelPricing.public_model == public_model)
    return (await session.execute(stmt)).scalars().first()


async def resolve_pricing(session: AsyncSession, public_model: str) -> PricingConfig:
    pricing = await get_model_pricing(session, public_model)
    if pricing is None:
        return PricingConfig(
            input_unit_price=0.0,
            cached_input_unit_price=0.0,
            output_unit_price=0.0,
            unit_tokens=1_000_000,
        )

    return PricingConfig(
        input_unit_price=pricing.input_unit_price,
        cached_input_unit_price=pricing.cached_input_unit_price,
        output_unit_price=pricing.output_unit_price,
        unit_tokens=pricing.unit_tokens,
    )


async def record_usage(
    session: AsyncSession,
    *,
    request_id: str,
    endpoint: str,
    usage_date: date,
    public_model: str,
    provider_id: int,
    api_key_id: int,
    token_usage: TokenUsage,
    latency_ms: int,
) -> tuple[float, float, float]:
    pricing = await resolve_pricing(session, public_model)
    total_cost = calculate_cost(token_usage, pricing)

    event = UsageEvent(
        request_id=request_id,
        usage_date=usage_date,
        endpoint=endpoint,
        public_model=public_model,
        provider_id=provider_id,
        api_key_id=api_key_id,
        input_tokens=token_usage.input_tokens,
        cached_input_tokens=token_usage.cached_input_tokens,
        output_tokens=token_usage.output_tokens,
        total_cost=total_cost,
        is_estimated=token_usage.is_estimated,
        latency_ms=latency_ms,
    )
    session.add(event)

    summary_stmt = select(DailyUsageSummary).where(
        and_(
            DailyUsageSummary.usage_date == usage_date,
            DailyUsageSummary.public_model == public_model,
            DailyUsageSummary.provider_id == provider_id,
            DailyUsageSummary.api_key_id == api_key_id,
        )
    )
    summary = (await session.execute(summary_stmt)).scalars().first()
    if summary is None:
        summary = DailyUsageSummary(
            usage_date=usage_date,
            public_model=public_model,
            provider_id=provider_id,
            api_key_id=api_key_id,
            input_tokens=token_usage.input_tokens,
            cached_input_tokens=token_usage.cached_input_tokens,
            output_tokens=token_usage.output_tokens,
            total_cost=total_cost,
            request_count=1,
            estimated_count=1 if token_usage.is_estimated else 0,
        )
        session.add(summary)
    else:
        summary.input_tokens += token_usage.input_tokens
        summary.cached_input_tokens += token_usage.cached_input_tokens
        summary.output_tokens += token_usage.output_tokens
        summary.total_cost += total_cost
        summary.request_count += 1
        if token_usage.is_estimated:
            summary.estimated_count += 1

    key = (await session.execute(select(ApiKey).where(ApiKey.id == api_key_id))).scalars().first()
    if key is None:
        raise ValueError(f"api key not found: {api_key_id}")

    balance_before = key.balance or 0.0
    key.balance = balance_before - total_cost
    balance_after = key.balance

    await session.commit()
    return total_cost, balance_before, balance_after
