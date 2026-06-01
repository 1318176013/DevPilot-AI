from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DevPilot AI"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://devpilot:devpilot123@192.168.194.2:5432/devpilot_ai"

    redis_url: str = "redis://192.168.194.2:6379/0"
    qdrant_url: str = "http://192.168.194.2:6333"
    backend_cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
