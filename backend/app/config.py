from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/startupinfo"

    # Auth
    secret_key: str = "changeme-use-a-long-random-string-in-production"
    algorithm: str = "HS256"
    access_token_expire_days: int = 7


    # App
    environment: str = "local"
    log_level: str = "info"
    api_v1_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
