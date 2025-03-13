from sqlalchemy import Column, Integer, Float, DateTime, String, Boolean, func, Index, cast, text
from ..database.config import Base
from datetime import datetime, timedelta

class ArcGISUsage(Base):
    __tablename__ = "arcgis_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String)  # e.g., "geocoding", "routing", "tile_request"
    credits_used = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    cached = Column(Boolean, default=False)  # Track if response was from cache
    request_path = Column(String)  # Store the request path for analysis
    
    # Create an index for timestamp and operation_type for efficient monthly queries
    __table_args__ = (
        Index('ix_usage_timestamp_op', timestamp, operation_type),
    )
    
    # Free tier monthly limits
    MONTHLY_LIMITS = {
        'tile_request': 2000000,  # 2M basemap tiles
        'geocoding': 20000,      # 20K geocoding operations
        'routing': 20000,        # 20K basic routes  
        'place_search': 500,     # 500 place searches
        'place_details': 100,    # 100 place attributes
        'elevation': 50000       # 50K elevation points
    }
    
    # Alert thresholds (percentage of monthly limit)
    ALERT_THRESHOLDS = {
        'warning': 0.80,  # 80% of limit
        'critical': 0.90, # 90% of limit
        'emergency': 0.95 # 95% of limit
    }
    
    @classmethod
    def get_daily_usage(cls, db) -> float:
        """Get total credits used in the last 24 hours"""
        today = func.now()
        yesterday = today - timedelta(days=1)
        result = db.query(func.sum(cls.credits_used))\
            .filter(cls.timestamp > yesterday)\
            .scalar()
        return float(result or 0)
    
    @classmethod
    def get_monthly_usage(cls, db, operation_type: str = None) -> dict:
        """Get usage count for the current month by operation type"""
        # Use database-agnostic date truncation
        if db.bind.dialect.name == 'sqlite':
            # SQLite date truncation using strftime
            start_of_month = text("date(CURRENT_DATE, 'start of month')")
        else:
            # PostgreSQL date_trunc
            start_of_month = func.date_trunc('month', func.current_date())

        query = db.query(
            cls.operation_type,
            func.count().label('count'),
            func.sum(cls.credits_used).label('credits'),
            func.sum(cast(cls.cached, Integer)).label('cache_hits')
        ).filter(cls.timestamp >= start_of_month)
        
        if operation_type:
            query = query.filter(cls.operation_type == operation_type)
            
        query = query.group_by(cls.operation_type)
        
        result = {op: {'count': 0, 'credits': 0.0, 'cache_hits': 0} 
                 for op in cls.MONTHLY_LIMITS.keys()}
        
        for row in query.all():
            result[row.operation_type] = {
                'count': row.count,
                'credits': float(row.credits or 0),
                'cache_hits': row.cache_hits
            }
            
        return result
    
    @classmethod
    def check_monthly_limit(cls, db, operation_type: str) -> tuple[bool, float, str]:
        """
        Check if operation would exceed monthly limit
        Returns: (is_within_limit, usage_percentage, alert_level)
        """
        if operation_type not in cls.MONTHLY_LIMITS:
            return True, 0.0, None
            
        usage = cls.get_monthly_usage(db, operation_type)
        current_count = usage[operation_type]['count']
        limit = cls.MONTHLY_LIMITS[operation_type]
        usage_percentage = (current_count / limit) * 100
        
        # Determine alert level
        alert_level = None
        for level, threshold in sorted(cls.ALERT_THRESHOLDS.items(), 
                                    key=lambda x: x[1], reverse=True):
            if usage_percentage >= (threshold * 100):
                alert_level = level
                break
        
        return current_count < limit, usage_percentage, alert_level
    
    @classmethod
    def get_usage_metrics(cls, db) -> dict:
        """Get comprehensive usage metrics for monitoring"""
        usage = cls.get_monthly_usage(db)
        metrics = {}
        
        for op_type, data in usage.items():
            limit = cls.MONTHLY_LIMITS.get(op_type, float('inf'))
            percentage = (data['count'] / limit * 100) if limit != float('inf') else 0
            cache_ratio = (data['cache_hits'] / data['count'] * 100) if data['count'] > 0 else 0
            
            metrics[op_type] = {
                'usage_count': data['count'],
                'monthly_limit': limit,
                'usage_percentage': percentage,
                'credits_used': data['credits'],
                'cache_hits': data['cache_hits'],
                'cache_ratio': cache_ratio
            }
        
        return metrics