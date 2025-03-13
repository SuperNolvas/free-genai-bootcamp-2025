from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database.config import engine, get_db
from .models import user, progress, content
from .routers import auth, progress as progress_router
from .core.config import get_settings

# Get settings instance
settings = get_settings()

# Create database tables
user.Base.metadata.create_all(bind=engine)
progress.Base.metadata.create_all(bind=engine)
content.Base.metadata.create_all(bind=engine)

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

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "online",
        "database": db_status,
        "version": settings.API_V1_PREFIX.strip("/")
    }
