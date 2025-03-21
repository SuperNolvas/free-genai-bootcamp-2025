from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
from pydantic import ConfigDict, Field
from pathlib import Path

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Language Voyager"
    DEBUG: bool = False
    
    # Frontend URL for email verification and password reset links
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Authentication - making these non-optional with secure defaults
    SECRET_KEY: str = "development-secret-key-change-in-production-00112233445566778899"
    JWT_SECRET_KEY: Optional[str] = None  # Will be initialized in __init__
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 240
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@db:5432/language_voyager"
    
    # Redis - ensure these have secure defaults
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Google Places
    GOOGLE_PLACES_API_KEY: Optional[str] = None
    
    # ArcGIS
    ARCGIS_API_KEY: Optional[str] = None
    ARCGIS_MAX_CREDITS_PER_DAY: float = 10.0
    ARCGIS_CACHE_DURATION: int = 24 * 60 * 60
    ARCGIS_FEATURE_LIMIT: int = 100
    
    # OpenRouter settings
    OPENROUTER_API_KEY: Optional[str] = None
    LLM_MODEL: Optional[str] = None  # Changed from OPENROUTER_DEFAULT_MODEL to match .env
    
    # Location Updates
    LOCATION_UPDATE_MIN_INTERVAL: float = 1.0
    LOCATION_UPDATE_BURST_LIMIT: int = 5
    LOCATION_UPDATE_BURST_PERIOD: int = 60
    LOCATION_CHANGE_MIN_DISTANCE: float = 1.0

    # Offline storage settings
    LOCAL_STORAGE_PATH: str = str(Path.home() / ".language-voyager" / "storage")
    OFFLINE_PACKAGE_TTL: int = 86400  # 24 hours
    MAX_OFFLINE_STORAGE_SIZE: int = 1024 * 1024 * 1024  # 1GB
    SYNC_RETRY_ATTEMPTS: int = 3
    SYNC_RETRY_DELAY: int = 5
    MIN_SYNC_INTERVAL: int = 300  # 5 minutes

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra="allow",
    )

    def __init__(self, **data):
        # Ensure we look for .env in the project root
        data['_env_file'] = str(Path(__file__).parent.parent.parent / '.env')
        super().__init__(**data)
        # Always use SECRET_KEY for JWT if JWT_SECRET_KEY is not explicitly set
        if self.JWT_SECRET_KEY is None:
            self.JWT_SECRET_KEY = self.SECRET_KEY
        
        # Set Redis URL if individual components are provided
        if not self.REDIS_URL and self.REDIS_HOST:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()