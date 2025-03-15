from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.config import Base
import uuid

class PointOfInterest(Base):
    __tablename__ = "points_of_interest"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    region_id = Column(String, ForeignKey("regions.id"), nullable=False)
    name = Column(String, nullable=False)
    local_name = Column(String)
    location = Column(JSON, nullable=False)  # {lat: float, lon: float}
    type = Column(String, nullable=False)
    difficulty = Column(Integer, default=1)  # 1-5 scale
    content_version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Content in multiple languages
    content = Column(JSON, nullable=False)  # {lang_code: {title, description, hints}}
    
    # Achievement criteria
    achievement_criteria = Column(JSON)  # {type: str, requirements: dict}
    points_value = Column(Integer, default=10)
    time_estimate = Column(Integer)  # estimated completion time in minutes
    
    # Learning objectives
    learning_objectives = Column(JSON)  # {vocabulary: [], grammar: [], cultural: []}
    
    # Metadata for offline sync
    sync_metadata = Column(JSON)  # {last_sync: timestamp, version: str}
    is_published = Column(Boolean, default=True)
    
    # Relationships
    region = relationship("Region", back_populates="points_of_interest")
    progress_records = relationship("UserProgress", back_populates="completed_pois")
    
    def to_dict(self):
        """Convert POI to dictionary format"""
        return {
            "id": self.id,
            "region_id": self.region_id,
            "name": self.name,
            "local_name": self.local_name,
            "location": self.location,
            "type": self.type,
            "difficulty": self.difficulty,
            "content": self.content,
            "achievement_criteria": self.achievement_criteria,
            "points_value": self.points_value,
            "time_estimate": self.time_estimate,
            "learning_objectives": self.learning_objectives,
            "content_version": self.content_version,
            "is_published": self.is_published,
            "sync_metadata": self.sync_metadata
        }
        
    def validate_completion(self, progress_data: dict) -> bool:
        """
        Validate if a user has completed this POI's requirements
        Args:
            progress_data: Dict containing user's progress data
        Returns:
            bool: Whether requirements are met
        """
        if not self.achievement_criteria:
            return True
            
        criteria = self.achievement_criteria
        if criteria["type"] == "visit":
            return True  # Just being there is enough
            
        elif criteria["type"] == "duration":
            min_duration = criteria["requirements"]["minutes"]
            actual_duration = progress_data.get("duration", 0)
            return actual_duration >= min_duration
            
        elif criteria["type"] == "interaction":
            required_interactions = criteria["requirements"]["count"]
            actual_interactions = len(progress_data.get("interactions", []))
            return actual_interactions >= required_interactions
            
        elif criteria["type"] == "quiz":
            required_score = criteria["requirements"]["min_score"]
            actual_score = progress_data.get("quiz_score", 0)
            return actual_score >= required_score
            
        return False