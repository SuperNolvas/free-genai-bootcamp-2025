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
    title: str
    description: str
    criteria: Dict
    achieved_at: datetime

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