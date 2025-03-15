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
    content_version: int = Field(1, description="Current content version")
    sync_metadata: Optional[Dict] = Field(None, description="Sync and version metadata")

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

class ContentItem(BaseModel):
    id: str
    content: Dict
    completed: bool = False
    mastery_level: float = 0
    difficulty_level: float

class LocalContext(BaseModel):
    dialect: str
    formality_level: str
    region_specific_customs: Dict
    visit_count: int
    difficulty_factors: Dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown of factors affecting content difficulty"
    )
    difficulty_progression: Dict[str, float] = Field(
        default_factory=dict,
        description="Projected difficulty levels for next visits"
    )

class VersionInfo(BaseModel):
    current_version: int = Field(..., description="Current content version")
    last_sync: Optional[str] = Field(None, description="Timestamp of last sync")
    update_type: Optional[str] = Field(None, description="Type of last update")

class ContentDeliveryResponse(BaseModel):
    vocabulary: List[ContentItem] = Field(default_factory=list)
    phrases: List[ContentItem] = Field(default_factory=list)
    dialogues: List[ContentItem] = Field(default_factory=list)
    cultural_notes: List[ContentItem] = Field(default_factory=list)
    difficulty_level: float = Field(..., ge=0, le=100)
    local_context: LocalContext = Field(default_factory=dict)
    version_info: VersionInfo = Field(...)