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

class POICoordinates(BaseModel):
    lat: float = Field(..., description="Latitude coordinate")
    lon: float = Field(..., description="Longitude coordinate")

class POIBase(BaseModel):
    id: str = Field(..., description="Unique POI identifier")
    name: str = Field(..., description="POI name in English")
    local_name: str = Field(..., description="POI name in local language")
    description: Optional[str] = Field(None, description="Brief description in English")
    local_description: Optional[str] = Field(None, description="Brief description in local language")
    poi_type: str = Field(..., description="Type of POI (e.g., restaurant, temple)")
    coordinates: POICoordinates = Field(..., description="Geographic coordinates")
    region_id: str = Field(..., description="ID of the region this POI belongs to")
    difficulty_level: float = Field(..., ge=0, le=100, description="Difficulty rating (0-100)")
    
class POIResponse(POIBase):
    content_ids: List[str] = Field(default_factory=list, description="Associated content/challenge IDs")
    metadata: Dict = Field(default_factory=dict, description="Additional POI metadata")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class POICreate(POIBase):
    pass  # All fields from POIBase are required for creation

class POIUpdate(BaseModel):
    name: Optional[str] = None
    local_name: Optional[str] = None
    description: Optional[str] = None
    local_description: Optional[str] = None
    poi_type: Optional[str] = None
    coordinates: Optional[POICoordinates] = None
    difficulty_level: Optional[float] = Field(None, ge=0, le=100)
    content_ids: Optional[List[str]] = None
    metadata: Optional[Dict] = None

class ContentDeliveryResponse(BaseModel):
    vocabulary: List[Dict] = Field(
        default_factory=list,
        description="Relevant vocabulary items for this POI"
    )
    phrases: List[Dict] = Field(
        default_factory=list,
        description="Useful phrases for this POI context"
    )
    dialogues: List[Dict] = Field(
        default_factory=list,
        description="Practice dialogues for this POI context"
    )
    cultural_notes: List[Dict] = Field(
        default_factory=list,
        description="Cultural information relevant to this POI"
    )
    difficulty_level: float = Field(..., ge=0, le=100)
    local_context: Dict = Field(
        default_factory=dict,
        description="Local context information like dialect, formality level"
    )