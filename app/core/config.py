from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "my-api-proxy"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_reload: bool = False

    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    http_timeout_seconds: int = 120
    request_cooldown_base_seconds: int = 5
    request_cooldown_max_seconds: int = 300
    client_api_keys: str = "change-me-client-key"
    admin_token: str = "change-me"

    default_currency: str = "USD"
    default_price_unit_tokens: int = 1_000_000


settings = Settings()
