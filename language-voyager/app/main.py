from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
from pathlib import Path
from .database.config import engine, get_db, SessionLocal
from .models import user, progress, content, arcgis_usage
from .routers import auth, progress as progress_router, map, conversation
from .core.config import get_settings
from .services.arcgis import ArcGISService
from .services.sync_manager import SyncManager
from .services.websocket import ConnectionManager, manager, LocationUpdate
from .services.location_manager import location_manager
from .services.geolocation import GeolocationService
from .auth.websocket_auth import authenticate_websocket_user
from .models.user import User
from starlette.websockets import WebSocketState
from jose import JWTError, jwt, ExpiredSignatureError
import json
import logging
import asyncio
import datetime
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

# Get settings instance
settings = get_settings()

# Create database tables
user.Base.metadata.create_all(bind=engine)
progress.Base.metadata.create_all(bind=engine)
content.Base.metadata.create_all(bind=engine)
arcgis_usage.Base.metadata.create_all(bind=engine)

# Store the sync manager instance
sync_manager = None

# Define frontend paths
frontend_path = Path(__file__).parent.parent / "frontend" / "public"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize managers
    global sync_manager
    db = next(get_db())
    sync_manager = SyncManager(db)
    websocket_manager = ConnectionManager()
    
    # Start services
    await sync_manager.start()
    
    yield
    
    # Cleanup on shutdown
    await sync_manager.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers with prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(progress_router.router, prefix="/api/v1")
app.include_router(map.router, prefix="/api/v1")  # Changed from "/api/v1/map"
app.include_router(conversation.router, prefix="/api/v1")

# Mount static files
app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(str(frontend_path / "index.html"))

@app.get("/dashboard.html")
async def serve_dashboard():
    return FileResponse(str(frontend_path / "dashboard.html"))

async def get_websocket_user(websocket: WebSocket) -> User:
    """Authenticate WebSocket connection and return user"""
    try:
        auth = websocket.headers.get("authorization", "")
        if not auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # Handle both "Bearer token" and raw token formats
        token = auth
        if auth.lower().startswith("bearer"):
            token = auth.split(" ")[1]
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            email = payload.get("sub")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
        except ExpiredSignatureError:
            logger.warning("WebSocket connection error: Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except JWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive user"
                )
            return user
        finally:
            db.close()

    except HTTPException as e:
        logger.warning(f"WebSocket connection error: {e.detail}")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {str(e)}")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_SERVER_ERROR)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Update WebSocket endpoint to handle async Redis properly
@app.websocket("/api/v1/map/ws/location")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time location updates"""
    user = None
    db = None
    geolocation = None
    
    try:
        # Get database session
        db = SessionLocal()
        
        # Authenticate using websocket-specific auth function
        user = await authenticate_websocket_user(websocket, db)
        
        # Accept the connection after authentication
        await websocket.accept()
        
        # Register connection with managers
        await manager.connect(websocket, user.id)
        location_manager.register_connection(user.id, websocket)
        
        # Initialize geolocation service
        geolocation = GeolocationService(websocket, user.id)
        
        # Start tracking with default configuration
        await geolocation.start_tracking({
            "highAccuracyMode": True,
            "timeout": 10000,
            "maximumAge": 30000,
            "minAccuracy": 20.0,
            "updateInterval": 5.0,
            "minimumDistance": 10.0,
            "backgroundMode": False,
            "powerSaveMode": False
        })
        
        while True:
            if websocket.client_state == WebSocketState.DISCONNECTED:
                break
                
            try:
                data = await websocket.receive_json()
                
                if "type" in data:
                    if data["type"] == "position_update":
                        # Handle position update from client
                        await geolocation.handle_location_update(data["position"])
                    elif data["type"] == "geolocation_error":
                        # Handle geolocation errors
                        await geolocation.handle_error(
                            data["error"].get("code", "UNKNOWN"),
                            data["error"].get("message", "Unknown error")
                        )
                    elif data["type"] == "config_update":
                        # Update tracking configuration
                        config = data.get("data", {}).get("config", {})
                        await geolocation.start_tracking(config)
                else:
                    logger.warning(f"Received unknown message type: {data}")
                    
            except WebSocketDisconnect:
                break
            except ValueError as e:
                if websocket.client_state != WebSocketState.DISCONNECTED:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                if websocket.client_state != WebSocketState.DISCONNECTED:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id if user else 'unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    finally:
        # Ensure cleanup happens even on unexpected errors
        try:
            if geolocation:
                await geolocation.stop_tracking()
            if user:
                await manager.disconnect(user.id)
                location_manager.unregister_connection(user.id)
            if db:
                db.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await location_manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown"""
    await location_manager.stop()
    await manager.cleanup()  # Add Redis cleanup

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    status = {
        "status": "online",
        "database": "unhealthy",
        "arcgis": "unchecked",
        "version": settings.API_V1_PREFIX.strip("/")
    }

    try:
        # Check database
        db.execute(text("SELECT 1"))
        status["database"] = "healthy"
        
        # Check ArcGIS if API key is configured
        if settings.ARCGIS_API_KEY:
            try:
                arcgis_service = ArcGISService(db)
                # Only test geocoding if database is healthy
                if status["database"] == "healthy":
                    await arcgis_service.geocode_location("Tokyo Station, Japan")
                status["arcgis"] = "healthy"
            except Exception as e:
                status["arcgis"] = f"unhealthy: {str(e)}"
                # Don't fail the health check for ArcGIS issues if database is healthy
                if "mapper" not in str(e):  # Ignore mapper initialization issues
                    status["arcgis"] = "degraded: service available but may have reduced functionality"
        else:
            status["arcgis"] = "unconfigured"
            
    except Exception as e:
        status["database"] = f"unhealthy: {str(e)}"
    
    # Only return 503 if database is unhealthy
    if status["database"] != "healthy":
        raise HTTPException(status_code=503, detail=status)
    
    return status
