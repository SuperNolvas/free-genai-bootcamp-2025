from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field

T = TypeVar('T')

class ErrorModel(BaseModel):
    code: str
    message: str
    details: Optional[str] = None

class ResponseModel(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    errors: Optional[List[ErrorModel]] = None

class GeolocationConfig(BaseModel):
    """Configuration model for geolocation settings"""
    # Core settings
    minAccuracy: float = Field(20.0, description="Minimum accuracy in meters for location updates")
    maxAccuracy: float = Field(100.0, description="Maximum acceptable accuracy in meters")
    updateInterval: float = Field(5.0, description="Update interval in seconds")
    
    # Power management
    backgroundMode: bool = Field(False, description="Enable background location tracking")
    powerSaveMode: bool = Field(False, description="Reduce update frequency to save power")
    highAccuracyMode: bool = Field(True, description="Use GPS for higher accuracy")
    
    # Performance settings
    minimumDistance: float = Field(10.0, description="Minimum distance (meters) between updates")
    maximumAge: int = Field(30000, description="Maximum age of cached position in milliseconds")
    timeout: int = Field(10000, description="Position request timeout in milliseconds")
    
    # Error handling
    retryInterval: float = Field(3.0, description="Retry interval for failed requests in seconds")
    maxRetries: int = Field(3, description="Maximum number of retry attempts")
    fallbackToNetwork: bool = Field(True, description="Fall back to network location if GPS fails")
    
    # Permission settings
    requireBackground: bool = Field(False, description="Require background location permission")
    requirePrecise: bool = Field(True, description="Require precise location permission")