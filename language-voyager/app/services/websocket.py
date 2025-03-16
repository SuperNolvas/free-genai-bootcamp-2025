from fastapi import WebSocket
from typing import Dict, Optional
from redis.asyncio import Redis
import json
import logging
import asyncio
from datetime import datetime
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class LocationUpdate:
    def __init__(self, lat: float, lon: float, region_id: Optional[str] = None, timestamp: Optional[float] = None):
        self.lat = lat
        self.lon = lon
        self.region_id = region_id
        self.timestamp = timestamp or datetime.utcnow().timestamp()

class ConnectionManager:
    def __init__(self):
        """Initialize the connection manager"""
        self.active_connections: Dict[int, WebSocket] = {}
        self.redis: Optional[Redis] = None
        self.redis_url = settings.REDIS_URL
        if not self.redis_url:
            raise ValueError("REDIS_URL is not configured in settings")
        
    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """Accept connection and store it"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Initialize Redis connection if needed
        if not self.redis:
            try:
                self.redis = Redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test the connection
                await self.redis.ping()
            except Exception as e:
                logger.error(f"Redis connection error: {e}")
                raise RuntimeError("Failed to connect to Redis") from e
    
    async def disconnect(self, user_id: int) -> None:
        """Remove connection"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close()
            except:
                pass
            del self.active_connections[user_id]
    
    async def update_user_location(self, user_id: int, lat: float, lon: float, region_id: Optional[str] = None) -> None:
        """Update user's location in Redis"""
        if not self.redis:
            return
            
        try:
            location_data = {
                "lat": lat,
                "lon": lon,
                "region_id": region_id,
                "timestamp": datetime.utcnow().timestamp()
            }
            await self.redis.hset(
                f"user:{user_id}:location",
                mapping=location_data
            )
            # Set expiry to prevent stale data
            await self.redis.expire(f"user:{user_id}:location", 3600)  # 1 hour
        except Exception as e:
            logger.error(f"Error updating location in Redis: {e}")
    
    async def get_user_location(self, user_id: int) -> Optional[LocationUpdate]:
        """Get user's last known location from Redis"""
        if not self.redis:
            return None
            
        try:
            location_data = await self.redis.hgetall(f"user:{user_id}:location")
            if location_data:
                return LocationUpdate(
                    lat=float(location_data["lat"]),
                    lon=float(location_data["lon"]),
                    region_id=location_data.get("region_id"),
                    timestamp=float(location_data["timestamp"])
                )
        except Exception as e:
            logger.error(f"Error getting location from Redis: {e}")
        return None
    
    async def cleanup(self) -> None:
        """Clean up connections and Redis"""
        # Close all WebSocket connections
        for user_id in list(self.active_connections.keys()):
            await self.disconnect(user_id)
        
        # Close Redis connection if it exists
        if self.redis:
            await self.redis.close()
            self.redis = None

# Create a singleton instance
manager = ConnectionManager()
