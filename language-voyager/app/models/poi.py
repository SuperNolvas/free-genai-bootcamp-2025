from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, func
from ..database.config import Base

class PointOfInterest(Base):
    __tablename__ = "points_of_interest"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    local_name = Column(String, nullable=False)
    description = Column(String)
    local_description = Column(String)
    poi_type = Column(String, nullable=False)  # e.g., restaurant, temple, shop
    coordinates = Column(JSON, nullable=False)  # {lat: float, lon: float}
    region_id = Column(String, ForeignKey('regions.id'), nullable=False)
    difficulty_level = Column(Float, nullable=False)
    content_ids = Column(JSON, default=list)  # List of associated content/challenge IDs
    poi_metadata = Column(JSON, default=dict)  # Additional metadata like opening hours, etc
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())