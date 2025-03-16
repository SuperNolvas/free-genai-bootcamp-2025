from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel
import json
import asyncio
import logging
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from .websocket import manager
from .location_manager import location_manager
from ..core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class GeolocationService:
    """Service for managing client-side geolocation"""
    
    def __init__(self, websocket: WebSocket, user_id: int):
        self.websocket = websocket
        self.user_id = user_id
        self.active = False
        self.last_position: Optional[Dict] = None
        self.error_count = 0
        self.update_task = None
        self.last_update_time = 0
        self.min_update_interval = 5.0  # Minimum time between updates in seconds

    async def send_json(self, data: Dict) -> None:
        """Safely send JSON data over WebSocket"""
        if self.websocket.client_state != WebSocketState.CONNECTED:
            return
        try:
            await self.websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            self.active = False

    async def start_tracking(self, config: Dict) -> None:
        """Start location tracking with the given configuration"""
        if self.websocket.client_state != WebSocketState.CONNECTED:
            return
            
        # Stop existing tracking if active
        if self.active:
            await self.stop_tracking()
            
        self.active = True
        self.error_count = 0
        
        # Update configuration
        self.min_update_interval = float(config.get("updateInterval", 5.0))
        if self.min_update_interval < 1.0:
            self.min_update_interval = 1.0  # Enforce minimum interval
        
        try:
            # Initialize tracking with config
            await self.send_json({
                "type": "geolocation_init",
                "config": {
                    "enableHighAccuracy": config.get("highAccuracyMode", True),
                    "timeout": config.get("timeout", 10000),
                    "maximumAge": config.get("maximumAge", 30000),
                    "minAccuracy": config.get("minAccuracy", 20.0),
                    "updateInterval": self.min_update_interval,
                    "minimumDistance": config.get("minimumDistance", 10.0)
                }
            })
            
            # Start update loop
            if not self.update_task or self.update_task.done():
                self.update_task = asyncio.create_task(self._update_loop(config))
        except Exception as e:
            logger.error(f"Error starting tracking: {e}")
            self.active = False
            await self.stop_tracking()

    async def stop_tracking(self) -> None:
        """Stop location tracking"""
        self.active = False
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
            self.update_task = None

    async def handle_location_update(self, data: Dict) -> None:
        """Process incoming location update"""
        if not self.active or self.websocket.client_state != WebSocketState.CONNECTED:
            return
            
        current_time = datetime.utcnow().timestamp()
        if current_time - self.last_update_time < self.min_update_interval:
            return  # Skip update if too soon
            
        try:
            # Reset error count on successful update
            self.error_count = 0
            self.last_position = data
            
            # Extract coordinates - handle nested structure correctly
            position = data.get("coords", {})  # The position data might be direct or in coords
            if not position and isinstance(data, dict):
                position = data.get("position", {}).get("coords", {})  # Try nested structure
            
            lat = position.get("latitude")
            lon = position.get("longitude")
            accuracy = position.get("accuracy")
            
            if lat is None or lon is None:
                raise ValueError("Missing latitude or longitude in position update")
            
            try:
                lat_float = float(lat)
                lon_float = float(lon)
                accuracy_float = float(accuracy) if accuracy is not None else None
            except (TypeError, ValueError):
                raise ValueError("Latitude and longitude must be numbers")
            
            # Update location in the location manager
            await manager.update_user_location(
                self.user_id,
                lat_float,
                lon_float,
                data.get("region_id"),
                accuracy_float
            )
            
            # Update last update time
            self.last_update_time = current_time
            
            # Don't send our own success response since manager.update_user_location already does
            
        except Exception as e:
            logger.error(f"Error processing location update: {e}")
            await self.handle_error("PROCESSING_ERROR", str(e))

    async def handle_error(self, code: str, message: str) -> None:
        """Handle geolocation errors"""
        if not self.active or self.websocket.client_state != WebSocketState.CONNECTED:
            return
            
        self.error_count += 1
        
        try:
            # Get error handling action from location manager
            action = await location_manager.handle_location_error(
                self.user_id,
                code,
                message
            )
            
            # Send action to client
            await self.send_json({
                "type": "geolocation_error",
                **action
            })
            
            # If we've hit max retries, fall back to network location
            if self.error_count >= settings.LOCATION_UPDATE_BURST_LIMIT:
                await self.send_json({
                    "type": "geolocation_fallback",
                    "message": "Falling back to network location"
                })
        except Exception as e:
            logger.error(f"Error handling geolocation error: {e}")

    async def _update_loop(self, config: Dict) -> None:
        """Background task for managing location updates"""
        try:
            while self.active and self.websocket.client_state == WebSocketState.CONNECTED:
                try:
                    current_time = datetime.utcnow().timestamp()
                    
                    # Only request position if enough time has passed
                    if current_time - self.last_update_time >= self.min_update_interval:
                        # Request position update from client
                        await self.send_json({
                            "type": "get_position"
                        })
                    
                    # Wait for configured interval
                    await asyncio.sleep(self.min_update_interval)
                    
                except Exception as e:
                    logger.error(f"Error in update loop: {e}")
                    await self.handle_error("UPDATE_LOOP_ERROR", str(e))
                    # Add exponential backoff on errors
                    await asyncio.sleep(min(30, self.min_update_interval * (2 ** self.error_count)))
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error in update loop: {e}")
            await self.handle_error("UPDATE_LOOP_ERROR", str(e))
        finally:
            self.active = False

# Create singleton instance
geolocation_service = GeolocationService