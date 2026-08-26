from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(min_length=1)
    session_secret: str = Field(min_length=32)
    database_url: str = "postgresql+asyncpg://knowly:knowly@localhost:5432/knowly"
    webapp_url: str = "http://localhost:5173"
    telegram_webhook_url: str | None = None
    webhook_secret: str | None = None
    allowed_origins: str = "http://localhost:5173"
    environment: str = "development"
    payments_enabled: bool = False
    auth_data_max_age_seconds: int = 300
    session_ttl_days: int = 30

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def async_database_url(self) -> str:
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
