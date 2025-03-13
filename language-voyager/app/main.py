from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database.config import engine, get_db
from .models import user, progress, content, arcgis_usage
from .routers import auth, progress as progress_router, map
from .core.config import get_settings
from .services.arcgis import ArcGISService

# Get settings instance
settings = get_settings()

# Create database tables
user.Base.metadata.create_all(bind=engine)
progress.Base.metadata.create_all(bind=engine)
content.Base.metadata.create_all(bind=engine)
arcgis_usage.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    progress_router.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    map.router,
    prefix=settings.API_V1_PREFIX
)

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
                # Try a simple geocoding request
                await arcgis_service.geocode_location("Tokyo Station, Japan")
                status["arcgis"] = "healthy"
            except Exception as e:
                status["arcgis"] = f"unhealthy: {str(e)}"
        else:
            status["arcgis"] = "unconfigured"
            
    except Exception as e:
        status["database"] = f"unhealthy: {str(e)}"
    
    if status["database"] != "healthy" or (
        settings.ARCGIS_API_KEY and status["arcgis"] != "healthy"
    ):
        raise HTTPException(status_code=503, detail=status)
    
    return status
