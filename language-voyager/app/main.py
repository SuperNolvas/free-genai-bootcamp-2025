from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database.config import engine, get_db
from .models import user, progress, content

# Create database tables
user.Base.metadata.create_all(bind=engine)
progress.Base.metadata.create_all(bind=engine)
content.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Language Voyager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Language Voyager API"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Try to make a simple query to test DB connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "online",
        "database": db_status
    }
