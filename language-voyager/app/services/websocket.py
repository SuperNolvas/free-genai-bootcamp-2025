from fastapi import WebSocket
from typing import Dict, List, Optional, Set, Union
import json
import asyncio
import time
from datetime import datetime
from pydantic import BaseModel, validator
from math import isfinite
from app.core.config import get_settings
from geopy.distance import geodesic
from starlette.websockets import WebSocketState
import logging
from redis.asyncio import Redis, RedisError
from collections import defaultdict

logger = logging.getLogger(__name__)

settings = get_settings()

class LocationUpdate(BaseModel):
    lat: float
    lon: float
    region_id: str
    timestamp: Optional[float] = None
    
    @validator('lat')
    def validate_latitude(cls, v):
        if not isfinite(v) or v < -90 or v > 90:
            raise ValueError('Invalid latitude')
        return v
        
    @validator('lon')
    def validate_longitude(cls, v):
        if not isfinite(v) or v < -180 or v > 180:
            raise ValueError('Invalid longitude')
        return v
        
    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v is None:
            return datetime.utcnow().timestamp()
        if not isfinite(v) or v < 0:
            raise ValueError('Invalid timestamp')
        return v

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def connect(self, websocket: WebSocket, user_id: int):
        self.active_connections[user_id] = websocket
        try:
            await self.redis.hset(f"user:{user_id}", "connected", "1")
        except RedisError as e:
            logger.error(f"Redis error on connect: {e}")

    async def disconnect(self, user_id: int):
        try:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            await self.redis.hdel(f"user:{user_id}", "connected")
        except RedisError as e:
            logger.error(f"Redis error on disconnect: {e}")

    async def update_user_location(self, user_id: int, lat: float, lon: float, region_id: Optional[int] = None) -> Dict:
        try:
            location_data = {
                "lat": str(lat),
                "lon": str(lon),
                "timestamp": str(int(time.time()))
            }
            if region_id:
                location_data["region_id"] = str(region_id)
            
            await self.redis.hset(f"user:{user_id}:location", mapping=location_data)
            return {"status": "ok", "location": location_data}
        except RedisError as e:
            logger.error(f"Redis error updating location: {e}")
            return {"status": "error", "message": "Failed to update location"}

manager = ConnectionManager()