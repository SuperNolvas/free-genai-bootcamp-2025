from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class ProgressUpdate(BaseModel):
    language: str
    region: str
    activity_type: str = Field(..., description="Type of activity: vocabulary, phrase, challenge, etc.")
    score: float = Field(..., ge=0, le=100, description="Score for the activity (0-100)")
    metadata: Optional[Dict] = Field(default=None, description="Additional activity-specific data")

class Achievement(BaseModel):
    id: str = Field(..., description="Unique achievement identifier")
    name: str = Field(..., description="Achievement name")
    description: str = Field(..., description="Achievement description")
    type: str = Field(..., description="Achievement type (e.g., poi_visit, content_mastery)")
    progress: float = Field(..., ge=0, le=100, description="Progress towards achievement (0-100)")
    completed: bool = Field(False, description="Whether the achievement is completed")
    completed_at: Optional[datetime] = Field(None, description="When the achievement was completed")
    metadata: Dict = Field(default_factory=dict, description="Additional achievement metadata")

class POIProgressUpdate(BaseModel):
    content_type: str = Field(..., description="Type of content interacted with")
    score: float = Field(..., ge=0, le=100, description="Score for this interaction")
    time_spent: int = Field(..., ge=0, description="Time spent in seconds")
    completed_items: List[str] = Field(default_factory=list, description="IDs of completed content items")

class ProgressResponse(BaseModel):
    language: str
    region: str
    proficiency_level: float
    completed_challenges: List[str]
    achievements: List[Achievement]
    last_activity: datetime

class OverallProgress(BaseModel):
    total_languages: int
    total_regions: int
    total_achievements: int
    languages: Dict[str, float]  # language -> proficiency level
    recent_activities: List[Dict]
    total_time_spent: int  # in minutes