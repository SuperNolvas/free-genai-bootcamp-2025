from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
from .database.config import engine, get_db
from .models import user, progress, content, arcgis_usage
from .routers import auth, progress as progress_router, map, conversation
from .core.config import get_settings
from .services.arcgis import ArcGISService
from .services.sync_manager import SyncManager
from .services.websocket import ConnectionManager, manager
from .services.location_manager import location_manager
from .auth.utils import get_current_user, get_current_active_user
from .models.user import User
from starlette.websockets import WebSocketState
from jose import JWTError, jwt

# Get settings instance
settings = get_settings()

# Create database tables
user.Base.metadata.create_all(bind=engine)
progress.Base.metadata.create_all(bind=engine)
content.Base.metadata.create_all(bind=engine)
arcgis_usage.Base.metadata.create_all(bind=engine)

# Store the sync manager instance
sync_manager = None

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
    lifespan=lifespan
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
app.include_router(
    auth.router,
    prefix=settings.API_V1_PREFIX
)
app.include_router(
    progress_router.router,
    prefix=settings.API_V1_PREFIX
)
app.include_router(
    conversation.router,
    prefix=settings.API_V1_PREFIX
)

# Include map router without WebSocket endpoint
map_router = map.router
app.include_router(
    map_router,
    prefix=settings.API_V1_PREFIX,
    tags=["map"]
)

# Register WebSocket endpoint directly
@app.websocket("/ws/location")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time location updates"""
    try:
        # Accept the connection first
        await websocket.accept()
        
        # Get auth token from headers
        token = None
        if "authorization" in websocket.headers:
            auth = websocket.headers["authorization"]
            scheme, token = auth.split()
            if scheme.lower() != "bearer":
                await websocket.close(code=4001, reason="Invalid authentication scheme")
                return
        
        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            return
            
        # Validate user using token verification logic
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            email = payload.get("sub")
            if email is None:
                await websocket.close(code=4001, reason="Invalid token payload")
                return
                
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                await websocket.close(code=4001, reason="User not found")
                return
                
            if not user.is_active:
                await websocket.close(code=4001, reason="User is inactive")
                return
                
            current_user = user
                
        except JWTError:
            await websocket.close(code=4001, reason="Invalid token")
            return
            
        # Register connection with manager (no accept needed)
        await manager.connect(websocket, current_user.id)
        
        try:
            while True:
                data = await websocket.receive_json()
                if websocket.client_state == WebSocketState.DISCONNECTED:
                    break
                    
                update_result = await manager.update_user_location(
                    current_user.id,
                    data.get('lat'),
                    data.get('lon'),
                    data.get('region_id')
                )
                if websocket.client_state != WebSocketState.DISCONNECTED:
                    await websocket.send_json(update_result)
                    
        except WebSocketDisconnect:
            await manager.disconnect(current_user.id)
        except Exception as e:
            await manager.disconnect(current_user.id)
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.close(code=4000, reason=str(e))
            
    except Exception as e:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=4000, reason=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await location_manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown"""
    await location_manager.stop()

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

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
