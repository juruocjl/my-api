from pydantic import BaseModel, Field


class ProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    base_url: str = Field(min_length=1, max_length=300)
    api_type: str = "openai"
    enabled: bool = True


class ProviderOut(BaseModel):
    id: int
    name: str
    base_url: str
    api_type: str
    enabled: bool

    model_config = {"from_attributes": True}


class ProviderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    base_url: str | None = Field(default=None, min_length=1, max_length=300)
    enabled: bool | None = None


class ApiKeyCreate(BaseModel):
    key_name: str = Field(min_length=1, max_length=100)
    api_key: str = Field(min_length=1, max_length=500)
    balance: float = 0.0
    enabled: bool = True


class ApiKeyUpdate(BaseModel):
    balance: float | None = None
    balance_delta: float | None = None
    enabled: bool | None = None


class ApiKeyOut(BaseModel):
    id: int
    provider_id: int
    key_name: str
    enabled: bool
    balance: float
    consecutive_failures: int
    cooldown_until: str | None
    last_error: str | None


class ModelRouteCreate(BaseModel):
    public_model: str
    provider_id: int
    upstream_model: str
    priority: int = 100
    enabled: bool = True


class ModelRouteOut(BaseModel):
    id: int
    public_model: str
    provider_id: int
    upstream_model: str
    priority: int
    enabled: bool

    model_config = {"from_attributes": True}


class ModelRouteUpdate(BaseModel):
    public_model: str | None = None
    provider_id: int | None = None
    upstream_model: str | None = None
    priority: int | None = None
    enabled: bool | None = None


class ModelPricingUpsert(BaseModel):
    public_model: str
    input_unit_price: float = 0
    cached_input_unit_price: float = 0
    output_unit_price: float = 0
    unit_tokens: int = 1_000_000


class ModelPricingOut(BaseModel):
    id: int
    public_model: str
    input_unit_price: float
    cached_input_unit_price: float
    output_unit_price: float
    unit_tokens: int

    model_config = {"from_attributes": True}
