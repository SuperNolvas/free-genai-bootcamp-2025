from fastapi import WebSocket
from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from pydantic import BaseModel
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class LocationError(BaseModel):
    code: str
    message: str
    timestamp: datetime
    retry_count: int = 0

class LocationState:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.error_states: Dict[int, LocationError] = {}
        self.power_states: Dict[int, str] = {}  # "normal", "power_save", "background"
        self.last_updates: Dict[int, datetime] = {}
        self.accuracy_levels: Dict[int, float] = {}

class LocationManager:
    def __init__(self):
        self.state = LocationState()
        self._cleanup_task = None
    
    async def start(self):
        """Start background tasks"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def stop(self):
        """Stop background tasks"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    def register_connection(self, user_id: int, websocket: WebSocket):
        """Register a new WebSocket connection"""
        self.state.active_connections[user_id] = websocket
        self.state.power_states[user_id] = "normal"
        self.state.last_updates[user_id] = datetime.utcnow()
    
    def unregister_connection(self, user_id: int):
        """Unregister a WebSocket connection"""
        self.state.active_connections.pop(user_id, None)
        self.state.error_states.pop(user_id, None)
        self.state.power_states.pop(user_id, None)
        self.state.last_updates.pop(user_id, None)
        self.state.accuracy_levels.pop(user_id, None)
    
    async def handle_location_error(self, user_id: int, error_code: str, message: str) -> Dict:
        """Handle location errors and determine retry strategy"""
        error = self.state.error_states.get(user_id)
        
        if error and error.code == error_code:
            error.retry_count += 1
        else:
            error = LocationError(
                code=error_code,
                message=message,
                timestamp=datetime.utcnow(),
                retry_count=1
            )
        
        self.state.error_states[user_id] = error
        
        # Determine action based on error type and retry count
        if error_code == "PERMISSION_DENIED":
            return {
                "action": "request_permission",
                "message": "Location permission required"
            }
        elif error_code == "POSITION_UNAVAILABLE":
            if error.retry_count <= 3:
                return {
                    "action": "retry",
                    "delay": error.retry_count * 2,
                    "message": "Retrying location update"
                }
            else:
                return {
                    "action": "fallback",
                    "message": "Using network location"
                }
        elif error_code == "TIMEOUT":
            return {
                "action": "adjust_settings",
                "settings": {
                    "timeout": min(20000, 10000 * error.retry_count),
                    "maximumAge": 60000
                }
            }
        
        return {"action": "error", "message": message}
    
    def update_power_state(self, user_id: int, location_config: Dict) -> Dict:
        """Update power state and adjust settings based on battery and activity"""
        current_state = self.state.power_states.get(user_id, "normal")
        new_state = current_state
        
        if location_config["powerSaveMode"]:
            new_state = "power_save"
            settings = {
                "updateInterval": 15.0,
                "highAccuracyMode": False,
                "maximumAge": 60000
            }
        elif location_config["backgroundMode"]:
            new_state = "background"
            settings = {
                "updateInterval": 30.0,
                "highAccuracyMode": False,
                "maximumAge": 120000
            }
        else:
            settings = {
                "updateInterval": 5.0,
                "highAccuracyMode": True,
                "maximumAge": 30000
            }
        
        if new_state != current_state:
            self.state.power_states[user_id] = new_state
            return {
                "state": new_state,
                "settings": settings
            }
        
        return None
    
    async def _periodic_cleanup(self):
        """Periodically clean up stale connections and errors"""
        while True:
            try:
                current_time = datetime.utcnow()
                error_timeout = current_time - timedelta(minutes=5)
                update_timeout = current_time - timedelta(minutes=2)
                
                # Clean up old error states
                self.state.error_states = {
                    user_id: error
                    for user_id, error in self.state.error_states.items()
                    if error.timestamp > error_timeout
                }
                
                # Check for stale connections
                for user_id, last_update in dict(self.state.last_updates).items():
                    if last_update < update_timeout:
                        logger.warning(f"Stale connection detected for user {user_id}")
                        self.unregister_connection(user_id)
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
            
            await asyncio.sleep(60)  # Run cleanup every minute

location_manager = LocationManager()