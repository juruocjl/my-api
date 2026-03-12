import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.load_balancer import (
    NoAvailableKeyError,
    NoRouteError,
    mark_key_failure,
    mark_key_success,
    resolve_route_and_key,
)
from app.core.timezone import business_today
from app.core.token_counter import parse_usage_from_upstream
from app.models.entities import ModelRoute
from app.services.provider_client import UpstreamRequestError, call_openai_compatible
from app.services.usage_service import record_usage

router = APIRouter(prefix="/v1", tags=["openai-compatible"])


@router.get("/models")
async def list_models(session: AsyncSession = Depends(get_db_session)) -> dict[str, Any]:
    routes = list(
        (await session.execute(select(ModelRoute).where(ModelRoute.enabled.is_(True)).order_by(ModelRoute.public_model.asc())))
        .scalars()
        .all()
    )
    model_ids = sorted({r.public_model for r in routes})
    return {
        "object": "list",
        "data": [{"id": mid, "object": "model", "owned_by": "my-api-proxy"} for mid in model_ids],
    }


async def _proxy_request(endpoint: str, request: Request, session: AsyncSession) -> dict[str, Any]:
    payload = await request.json()
    public_model = payload.get("model")
    if not public_model:
        raise HTTPException(status_code=400, detail="model is required")

    if payload.get("stream") is True:
        raise HTTPException(status_code=400, detail="stream mode is not supported in this version")

    request_id = str(uuid.uuid4())
    started = time.time()

    try:
        route, provider, key = await resolve_route_and_key(session, public_model)
    except NoRouteError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NoAvailableKeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        call_result = await call_openai_compatible(
            base_url=provider.base_url,
            api_key=key.api_key,
            endpoint=endpoint,
            payload=payload,
            upstream_model=route.upstream_model,
        )
        mark_key_success(key)
        await session.commit()
    except UpstreamRequestError as exc:
        if exc.status_code in {429, 500, 502, 503, 504}:
            mark_key_failure(key, str(exc))
            await session.commit()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    response_json = dict(call_result.json_body)
    response_json["model"] = public_model

    token_usage = parse_usage_from_upstream(
        endpoint=endpoint,
        payload=payload,
        response_json=response_json,
        model_name=public_model,
    )
    latency_ms = int((time.time() - started) * 1000)

    total_cost, balance_before, balance_after = await record_usage(
        session,
        request_id=request_id,
        endpoint=endpoint,
        usage_date=business_today(),
        public_model=public_model,
        provider_id=provider.id,
        api_key_id=key.id,
        token_usage=token_usage,
        latency_ms=latency_ms,
    )

    response_json.setdefault("usage", {})
    response_json["usage"]["x_proxy_cached_input_tokens"] = token_usage.cached_input_tokens
    response_json["usage"]["x_proxy_cost"] = total_cost
    response_json["x_proxy"] = {
        "request_id": request_id,
        "provider_id": provider.id,
        "api_key_id": key.id,
        "api_key_balance_before": balance_before,
        "api_key_balance_after": balance_after,
        "latency_ms": latency_ms,
        "estimated_usage": token_usage.is_estimated,
    }

    return response_json


@router.post("/chat/completions")
async def chat_completions(request: Request, session: AsyncSession = Depends(get_db_session)) -> dict[str, Any]:
    return await _proxy_request(endpoint="/v1/chat/completions", request=request, session=session)


@router.post("/embeddings")
async def embeddings(request: Request, session: AsyncSession = Depends(get_db_session)) -> dict[str, Any]:
    return await _proxy_request(endpoint="/v1/embeddings", request=request, session=session)
