from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
from pydantic import ConfigDict
from pathlib import Path

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Language Voyager"
    DEBUG: bool = False
    
    # Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # ArcGIS
    ARCGIS_API_KEY: str | None = None
    ARCGIS_MAX_CREDITS_PER_DAY: float = 10.0  # Conservative daily limit
    ARCGIS_CACHE_DURATION: int = 24 * 60 * 60  # Cache responses for 24 hours
    ARCGIS_FEATURE_LIMIT: int = 100  # Limit features per request
    
    # OpenRouter settings
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_DEFAULT_MODEL: Optional[str] = None  # e.g. "mistralai/mistral-7b" or "anthropic/claude-2"
    
    # Location Updates
    LOCATION_UPDATE_MIN_INTERVAL: float = 1.0  # Minimum seconds between updates
    LOCATION_UPDATE_BURST_LIMIT: int = 5  # Maximum burst updates allowed
    LOCATION_UPDATE_BURST_PERIOD: int = 60  # Period (in seconds) for burst limit
    LOCATION_CHANGE_MIN_DISTANCE: float = 1.0  # Minimum distance (meters) required between updates

    # Offline storage settings
    LOCAL_STORAGE_PATH: str = str(Path.home() / ".language-voyager" / "storage")
    OFFLINE_PACKAGE_TTL: int = 86400  # 24 hours in seconds
    MAX_OFFLINE_STORAGE_SIZE: int = 1024 * 1024 * 1024  # 1GB
    SYNC_RETRY_ATTEMPTS: int = 3
    SYNC_RETRY_DELAY: int = 5  # seconds
    MIN_SYNC_INTERVAL: int = 300  # 5 minutes between syncs

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"  # Allow extra fields in environment
    )

@lru_cache()
def get_settings() -> Settings:
    """
    Creates a cached instance of settings.
    Use this function to get settings throughout the application.
    """
    return Settings()