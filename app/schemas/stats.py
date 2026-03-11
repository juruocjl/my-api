from datetime import date, datetime

from pydantic import BaseModel


class DailyUsageItem(BaseModel):
    usage_date: date
    public_model: str
    provider_id: int
    api_key_id: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    total_cost: float
    request_count: int
    estimated_count: int


class DailyUsageTotals(BaseModel):
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    total_cost: float
    request_count: int
    estimated_count: int


class DailyUsageResponse(BaseModel):
    items: list[DailyUsageItem]
    totals: DailyUsageTotals


class UsageEventItem(BaseModel):
    request_id: str
    created_at: datetime
    endpoint: str
    public_model: str
    provider_id: int
    api_key_id: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    total_cost: float
    is_estimated: bool
    latency_ms: int


class UsageEventResponse(BaseModel):
    items: list[UsageEventItem]
