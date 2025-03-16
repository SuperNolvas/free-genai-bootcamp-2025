from fastapi import WebSocket
from typing import Dict, Optional, Any
from redis.asyncio import Redis
from starlette.websockets import WebSocketState
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
        
    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """Store connection - does NOT accept it"""
        if user_id in self.active_connections:
            # Clean up existing connection first
            await self.disconnect(user_id)
            
        self.active_connections[user_id] = websocket
        
        # Initialize Redis connection if needed
        if self.redis_url and not self.redis:
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
                self.redis = None
    
    async def disconnect(self, user_id: int) -> None:
        """Remove connection"""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.close()
            except Exception as e:
                logger.error(f"Error closing websocket: {e}")
            finally:
                del self.active_connections[user_id]
                # Clean up Redis data
                try:
                    self.redis.delete(f"user_location:{user_id}")
                except Exception as e:
                    logger.error(f"Error cleaning up Redis data: {e}")
    
    async def send_to_user(self, user_id: int, data: Dict[str, Any]) -> None:
        """Send data to a specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_json(data)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    await self.disconnect(user_id)
    
    async def update_user_location(self, user_id: int, lat: float, lon: float, region_id: Optional[str] = None, accuracy: Optional[float] = None) -> None:
        """Update user's location in Redis"""
        if not self.redis:
            return
            
        try:
            # Validate inputs
            if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                raise ValueError("Latitude and longitude must be numbers")
                
            location_data = {
                "lat": str(float(lat)),
                "lon": str(float(lon)),
                "timestamp": str(datetime.utcnow().timestamp())
            }
            
            if region_id is not None:
                location_data["region_id"] = str(region_id)
                
            # Update location in Redis
            key = f"user:{user_id}:location"
            await self.redis.hset(key, mapping=location_data)
            await self.redis.expire(key, 3600)  # 1 hour TTL
            
            # Send confirmation to user with coordinates
            await self.send_to_user(user_id, {
                "type": "location_update",
                "status": "ok",
                "coords": {
                    "latitude": lat,
                    "longitude": lon,
                    "accuracy": accuracy
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid location data: {e}")
            if user_id in self.active_connections:
                await self.send_to_user(user_id, {
                    "type": "error",
                    "message": str(e)
                })
        except Exception as e:
            logger.error(f"Error updating location in Redis: {e}")
    
    async def get_user_location(self, user_id: int) -> Optional[LocationUpdate]:
        """Get user's last known location from Redis"""
        if not self.redis:
            return None
            
        try:
            location_data = await self.redis.hgetall(f"user:{user_id}:location")
            if location_data and "lat" in location_data and "lon" in location_data:
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
            try:
                await self.redis.close()
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self.redis = None

# Create a singleton instance
manager = ConnectionManager()
