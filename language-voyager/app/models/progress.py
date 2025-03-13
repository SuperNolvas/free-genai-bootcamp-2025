from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.config import Base

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    language = Column(String)  # e.g., "japanese", "korean"
    region = Column(String)    # e.g., "tokyo", "kansai"
    proficiency_level = Column(Float)  # Decimal score of proficiency
    completed_challenges = Column(JSON)  # Store completed challenge IDs and scores
    vocabulary_mastered = Column(JSON)  # Store mastered vocabulary with timestamps
    last_location = Column(String)  # Last game location coordinates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user
    user = relationship("User", back_populates="progress")