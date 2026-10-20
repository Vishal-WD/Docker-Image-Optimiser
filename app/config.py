from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    APP_NAME: str = "Docker Image Optimizer & Benchmarker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PostgreSQL Database URL
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/optimizer_db"
    # Fallback SQLite DB for local unit tests without live Postgres
    USE_SQLITE_FALLBACK: bool = True
    SQLITE_URL: str = "sqlite:///./optimizer_local.db"

    # Docker optimization benchmark baseline figures
    UNOPTIMIZED_SIZE_MB: float = 1520.0
    OPTIMIZED_SIZE_MB: float = 142.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
