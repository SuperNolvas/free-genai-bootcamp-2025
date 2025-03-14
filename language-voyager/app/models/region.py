from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, func
from ..database.config import Base

class Region(Base):
    __tablename__ = "regions"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    local_name = Column(String, nullable=False)
    description = Column(String)
    languages = Column(JSON, nullable=False)  # List of supported languages and requirements
    bounds = Column(JSON, nullable=False)     # Geographic bounds
    center = Column(JSON, nullable=False)     # Center coordinates
    difficulty_level = Column(Float, nullable=False)
    requirements = Column(JSON)               # Requirements to unlock region
    total_pois = Column(Integer, default=0)
    total_challenges = Column(Integer, default=0)
    recommended_level = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())