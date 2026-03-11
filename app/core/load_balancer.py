from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import ApiKey, ModelRoute, Provider


class NoRouteError(Exception):
    pass


class NoAvailableKeyError(Exception):
    pass


async def resolve_route_and_key(
    session: AsyncSession,
    public_model: str,
) -> tuple[ModelRoute, Provider, ApiKey]:
    route_stmt = (
        select(ModelRoute, Provider)
        .join(Provider, ModelRoute.provider_id == Provider.id)
        .where(ModelRoute.public_model == public_model, ModelRoute.enabled.is_(True), Provider.enabled.is_(True))
        .order_by(ModelRoute.priority.asc())
    )
    route_rows = (await session.execute(route_stmt)).all()
    if not route_rows:
        raise NoRouteError(f"No route configured for model: {public_model}")

    now = datetime.utcnow()
    for route, provider in route_rows:
        key_stmt = (
            select(ApiKey)
            .where(ApiKey.provider_id == provider.id, ApiKey.enabled.is_(True))
            .order_by(ApiKey.weight.desc(), ApiKey.id.asc())
        )
        keys = list((await session.execute(key_stmt)).scalars().all())
        available = [
            k
            for k in keys
            if (not k.cooldown_until or k.cooldown_until <= now) and (k.balance or 0.0) > 0
        ]
        if not available:
            continue

        selected = available[0]
        return route, provider, selected

    raise NoAvailableKeyError(f"No available API key for model: {public_model}")


def mark_key_success(key: ApiKey) -> None:
    key.consecutive_failures = 0
    key.cooldown_until = None
    key.last_error = None
    key.last_used_at = datetime.utcnow()


def mark_key_failure(key: ApiKey, error_message: str) -> None:
    key.consecutive_failures = (key.consecutive_failures or 0) + 1
    key.last_error = error_message[:1000]

    cooldown_seconds = min(
        settings.request_cooldown_max_seconds,
        settings.request_cooldown_base_seconds * (2 ** min(key.consecutive_failures, 8)),
    )
    key.cooldown_until = datetime.utcnow() + timedelta(seconds=cooldown_seconds)
