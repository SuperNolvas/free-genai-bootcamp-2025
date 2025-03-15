from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.config import Base

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    region_id = Column(String, ForeignKey("regions.id"))
    language = Column(String)  # e.g., "japanese", "korean"
    region = Column(String)    # e.g., "tokyo", "kansai"
    proficiency_level = Column(Float)  # Decimal score of proficiency
    completed_challenges = Column(JSON)  # Store completed challenge IDs and scores
    vocabulary_mastered = Column(JSON)  # Store mastered vocabulary with timestamps
    last_location = Column(String)  # Last game location coordinates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add POI tracking
    poi_progress = Column(JSON, default=dict, nullable=False)  # Store POI visit history and completion status
    content_mastery = Column(JSON, default=dict, nullable=False)  # Track content mastery by type
    achievements = Column(JSON, default=list, nullable=False)  # Store earned achievements
    
    # Relationships
    user = relationship("User", back_populates="progress")
    region = relationship("Region", back_populates="user_progress")