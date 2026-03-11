from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


class UpstreamRequestError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(message)


@dataclass
class ProviderCallResult:
    status_code: int
    json_body: dict[str, Any]


async def call_openai_compatible(
    *,
    base_url: str,
    api_key: str,
    endpoint: str,
    payload: dict[str, Any],
    upstream_model: str,
) -> ProviderCallResult:
    body = dict(payload)
    body["model"] = upstream_model

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    timeout = httpx.Timeout(settings.http_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(f"{base_url.rstrip('/')}" + endpoint, json=body, headers=headers)

    try:
        data = response.json()
    except Exception:
        data = {"error": {"message": response.text or "Invalid JSON from upstream"}}

    if response.status_code >= 400:
        msg = data.get("error", {}).get("message") or f"upstream error {response.status_code}"
        raise UpstreamRequestError(status_code=response.status_code, message=msg)

    return ProviderCallResult(status_code=response.status_code, json_body=data)
