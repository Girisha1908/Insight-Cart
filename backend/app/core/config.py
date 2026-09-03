"""Application settings loaded from environment / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the InsightCart backend.

    Values are read from environment variables, falling back to the values
    declared below. A local `.env` file (git-ignored) can override them.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    DATABASE_URL: str = (
        "postgresql+psycopg://insightcart:insightcart@localhost:5432/insightcart"
    )
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ENVIRONMENT: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
