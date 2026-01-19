"""Application configuration."""

import importlib.metadata
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the backend directory (parent of app directory)
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"


def get_app_version() -> str:
    """Get the application version from package metadata."""
    try:
        return importlib.metadata.version("meal-planner-backend")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "Meal Planner API"
    DEBUG: bool = False

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./meal_planner.db"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:3080,http://localhost:5173"

    # Backend URL for generating absolute URLs
    BACKEND_URL: str = "http://localhost:8180"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB

    # Email (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # SendGrid (optional)
    SENDGRID_API_KEY: str = ""

    # OpenAI (optional)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # Recipe Images
    DEFAULT_RECIPE_IMAGE: str = "/uploads/recipes/missing-image.jpg"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def app_version(self) -> str:
        """Get the application version dynamically."""
        return get_app_version()

    def __getattr__(self, name: str) -> str:  # type: ignore[no-untyped-def]
        """Handle backward compatibility for APP_VERSION attribute."""
        if name == "APP_VERSION":
            return self.app_version
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


settings = Settings()
