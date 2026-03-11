import hmac

from fastapi import Header, HTTPException, Query

from app.core.config import settings


def _extract_bearer_token(value: str | None) -> str | None:
    if not value:
        return None
    prefix = "Bearer "
    if value.startswith(prefix):
        token = value[len(prefix) :].strip()
        return token or None
    return None


def _compare_against_allowed(token: str, allowed: set[str]) -> bool:
    return any(hmac.compare_digest(token, candidate) for candidate in allowed)


def _get_client_api_keys() -> set[str]:
    return {item.strip() for item in settings.client_api_keys.split(",") if item.strip()}


async def require_admin_auth(
    x_admin_token: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> None:
    expected = settings.admin_token
    provided = x_admin_token or _extract_bearer_token(authorization) or token

    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="unauthorized")


async def require_openai_auth(authorization: str | None = Header(default=None)) -> None:
    token = _extract_bearer_token(authorization)
    allowed = _get_client_api_keys()

    if not token or not allowed or not _compare_against_allowed(token, allowed):
        raise HTTPException(status_code=401, detail="invalid_api_key")
