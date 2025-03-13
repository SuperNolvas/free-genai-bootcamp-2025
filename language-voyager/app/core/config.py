from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
from pydantic import ConfigDict

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