from fastapi import WebSocket
from typing import Dict, List, Optional, Set
import json
import asyncio
from datetime import datetime
from pydantic import BaseModel, validator
from math import isfinite
from app.core.config import get_settings
import redis
from geopy.distance import geodesic
from starlette.websockets import WebSocketState

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
        self.user_locations: Dict[int, Dict] = {}
        self.region_users: Dict[str, Set[int]] = {}
        self.redis_client = redis.from_url(settings.REDIS_URL)
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """Register a WebSocket connection and send welcome message"""
        self.active_connections[user_id] = websocket
        await websocket.send_json({
            "type": "connected",
            "message": "Successfully connected to location service",
            "user_id": user_id
        })
        
    async def disconnect(self, user_id: int):
        """Handle disconnection cleanup"""
        websocket = self.active_connections.pop(user_id, None)
        location = self.user_locations.pop(user_id, None)
        if location:
            region_id = location.get('region_id')
            if region_id in self.region_users:
                self.region_users[region_id].discard(user_id)
                
    async def check_rate_limit(self, user_id: int) -> bool:
        """Check if user has exceeded rate limits"""
        now = datetime.utcnow().timestamp()
        key_last = f"location:last:{user_id}"
        key_burst = f"location:burst:{user_id}"
        
        # Check minimum interval
        last_update = self.redis_client.get(key_last)
        if last_update:
            time_since = now - float(last_update)
            if time_since < settings.LOCATION_UPDATE_MIN_INTERVAL:
                return False
                
        # Check burst limit
        burst_count = self.redis_client.incr(key_burst)
        if burst_count == 1:
            self.redis_client.expire(key_burst, settings.LOCATION_UPDATE_BURST_PERIOD)
        elif burst_count > settings.LOCATION_UPDATE_BURST_LIMIT:
            return False
            
        self.redis_client.set(key_last, str(now))
        return True
        
    def check_min_distance(self, user_id: int, lat: float, lon: float) -> bool:
        """Check if new location meets minimum distance requirement"""
        if user_id not in self.user_locations:
            return True
            
        last_loc = self.user_locations[user_id]
        if 'lat' not in last_loc or 'lon' not in last_loc:
            return True
            
        last_point = (last_loc['lat'], last_loc['lon'])
        new_point = (lat, lon)
        distance = geodesic(last_point, new_point).meters
        
        return distance >= settings.LOCATION_CHANGE_MIN_DISTANCE
        
    async def update_user_location(self, user_id: int, lat: float, lon: float, region_id: str) -> Dict:
        """Update stored user location and notify relevant users"""
        # Rate limiting and validation
        if not await self.check_rate_limit(user_id):
            return {"error": "Rate limit exceeded"}
            
        if not self.check_min_distance(user_id, lat, lon):
            return {"error": "Location update too frequent for distance"}
            
        # Update location
        self.user_locations[user_id] = {
            'lat': lat,
            'lon': lon,
            'region_id': region_id,
            'last_update': datetime.utcnow().isoformat()
        }
        
        # Update region tracking
        old_region = next((reg for reg, users in self.region_users.items() 
                         if user_id in users), None)
        if old_region and old_region != region_id:
            self.region_users[old_region].discard(user_id)
            
        if region_id not in self.region_users:
            self.region_users[region_id] = set()
        self.region_users[region_id].add(user_id)
        
        # Notify other users in the same region
        await self.broadcast_to_region({
            'type': 'user_location',
            'user_id': user_id,
            'location': self.user_locations[user_id]
        }, region_id, exclude_user=user_id)
        
        return {"success": True}

    async def broadcast_to_region(self, message: Dict, region_id: str, exclude_user: Optional[int] = None):
        """Send message to all users in a region except the excluded user"""
        if region_id not in self.region_users:
            return
            
        json_message = json.dumps(message)
        for user_id in self.region_users[region_id]:
            if user_id != exclude_user and user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].send_text(json_message)
                except:
                    await self.handle_disconnect(user_id)
                    
    async def handle_disconnect(self, user_id: int):
        """Handle unexpected disconnections"""
        self.disconnect(user_id)
        # Could add reconnection logic here if needed

manager = ConnectionManager()