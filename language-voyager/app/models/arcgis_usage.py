from sqlalchemy import Column, Integer, Float, DateTime, String, func
from ..database.config import Base

class ArcGISUsage(Base):
    __tablename__ = "arcgis_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String)  # e.g., "geocoding", "routing", "tile_request"
    credits_used = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    @classmethod
    def get_daily_usage(cls, db) -> float:
        """Get total credits used in the last 24 hours"""
        today = func.now()
        yesterday = today - func.interval('1 day')
        result = db.query(func.sum(cls.credits_used))\
            .filter(cls.timestamp > yesterday)\
            .scalar()
        return float(result or 0)