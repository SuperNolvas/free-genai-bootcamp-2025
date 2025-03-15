from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.config import Base

# Join table for UserProgress and PointOfInterest with explicit foreign key constraints
progress_poi_association = Table(
    'progress_poi_association',
    Base.metadata,
    Column('progress_id', Integer, ForeignKey('user_progress.id', ondelete='CASCADE'), primary_key=True),
    Column('poi_id', String, ForeignKey('points_of_interest.id', ondelete='CASCADE'), primary_key=True)
)

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    region_id = Column(String, ForeignKey("regions.id"))
    language = Column(String)  # e.g., "japanese", "korean"
    region_name = Column(String)    # renamed from region to avoid conflict
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
    region = relationship("Region", back_populates="user_progress", foreign_keys=[region_id])
    completed_pois = relationship(
        "PointOfInterest",
        secondary=progress_poi_association,
        back_populates="progress_records",
        lazy="joined"  # Optimize loading
    )