"""Centralized application configuration using Pydantic Settings."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "DuitKu Backend"
    ENVIRONMENT: str = "development"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Firebase
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_CLIENT_ID: str = ""
    FIREBASE_SERVICE_ACCOUNT_KEY_PATH: str = "serviceAccountKey.json"
    FIREBASE_API_KEY: str = ""

    # JWT (internal session tokens)
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Firestore
    FIRESTORE_PAGE_LIMIT: int = 20
    FIRESTORE_MAX_PAGE_LIMIT: int = 100

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse the comma-separated ALLOWED_ORIGINS into a list."""
        origins = [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        return origins


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton across the app)."""
    return Settings()


settings = get_settings()

