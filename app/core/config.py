"""Application configuration via environment variables.

Uses pydantic-settings to load values from environment and optional ``.env``.
Prefix: ``EVENTFINDER_`` (e.g., ``EVENTFINDER_DATABASE_PATH``).
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the API service."""
    app_name: str = "Event Finder API"
    database_path: str = "./event_finder.db"
    backend_cors_origins: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://0.0.0.0:8000",
    ]

    # pydantic-settings v2 configuration
    model_config = SettingsConfigDict(
        env_prefix="EVENTFINDER_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
