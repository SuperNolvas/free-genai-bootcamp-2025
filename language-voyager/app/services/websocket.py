from fastapi import WebSocket
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime
from pydantic import BaseModel, validator
from math import isfinite

class LocationUpdate(BaseModel):
    lat: float
    lon: float
    region_id: str
    
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

class ConnectionManager:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store user locations
        self.user_locations: Dict[int, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a new websocket for a user"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    async def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect a websocket for a user"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                # Clean up location data when user has no active connections
                if user_id in self.user_locations:
                    del self.user_locations[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific user's connections"""
        if user_id not in self.active_connections:
            return
            
        dead_connections = []
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except RuntimeError:
                dead_connections.append(connection)
        
        # Clean up dead connections
        for dead_conn in dead_connections:
            self.active_connections[user_id].remove(dead_conn)
    
    async def broadcast_to_region(self, message: dict, region_id: str, exclude_user: Optional[int] = None):
        """Broadcast message to all users in a specific region"""
        for user_id, location in self.user_locations.items():
            if user_id != exclude_user and location.get('region_id') == region_id:
                await self.send_personal_message(message, user_id)
    
    async def update_user_location(self, user_id: int, lat: float, lon: float, region_id: str):
        """Update stored user location and notify relevant users"""
        self.user_locations[user_id] = {
            'lat': lat,
            'lon': lon,
            'region_id': region_id,
            'last_update': datetime.utcnow().isoformat()
        }
        
        # Notify other users in the same region
        await self.broadcast_to_region({
            'type': 'user_location',
            'user_id': user_id,
            'location': self.user_locations[user_id]
        }, region_id, exclude_user=user_id)

# Global connection manager instance
manager = ConnectionManager()