from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class RegionLanguage(BaseModel):
    language_code: str = Field(..., description="ISO language code (e.g., 'ja' for Japanese)")
    name: str = Field(..., description="Language name in English")
    local_name: str = Field(..., description="Language name in its own script")
    required_level: float = Field(0.0, description="Minimum proficiency level required (0-100)")

class Region(BaseModel):
    id: str = Field(..., description="Unique region identifier")
    name: str = Field(..., description="Region name in English")
    local_name: str = Field(..., description="Region name in local language")
    description: str = Field(..., description="Brief description of the region")
    languages: List[RegionLanguage] = Field(..., description="Languages available in this region")
    bounds: Dict[str, float] = Field(..., description="Geographic bounds (north, south, east, west)")
    center: Dict[str, float] = Field(..., description="Center point coordinates")
    difficulty_level: float = Field(..., ge=0, le=100, description="Overall difficulty rating (0-100)")
    is_available: bool = Field(True, description="Whether the region is unlocked for the user")
    requirements: Optional[Dict[str, float]] = Field(None, description="Requirements to unlock if not available")
    total_pois: int = Field(..., description="Number of points of interest")
    total_challenges: int = Field(..., description="Number of available challenges")
    recommended_level: float = Field(..., description="Recommended proficiency level")
    created_at: Optional[datetime] = Field(None, description="When the region was created")
    updated_at: Optional[datetime] = Field(None, description="When the region was last updated")