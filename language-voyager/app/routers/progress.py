from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime
from typing import List

from ..database.config import get_db
from ..models.user import User
from ..models.progress import UserProgress
from ..models.poi import PointOfInterest
from ..auth.utils import get_current_active_user
from ..core.schemas import ResponseModel
from .schemas.progress import (
    ProgressUpdate,
    ProgressResponse,
    Achievement,
    OverallProgress,
    POIProgressUpdate
)
from ..services.cache import cache

router = APIRouter(
    prefix="/progress",
    tags=["progress"],
    dependencies=[Depends(get_current_active_user)]
)

@router.get("/", response_model=ResponseModel[OverallProgress])
async def get_overall_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    progress = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()
    
    if not progress:
        return ResponseModel(
            success=True,
            message="No progress recorded yet",
            data=OverallProgress(
                total_languages=0,
                total_regions=0,
                total_achievements=0,
                languages={},
                recent_activities=[],
                total_time_spent=0
            )
        )
    
    # Aggregate progress data
    languages = {}
    regions = set()
    achievements = []
    recent_activities = []
    total_time = 0
    
    for p in progress:
        languages[p.language] = p.proficiency_level
        regions.add(p.region)
        if p.completed_challenges:
            recent_activities.extend(p.completed_challenges)
    
    return ResponseModel(
        success=True,
        message="Progress retrieved successfully",
        data=OverallProgress(
            total_languages=len(languages),
            total_regions=len(regions),
            total_achievements=len(achievements),
            languages=languages,
            recent_activities=recent_activities[-10:],  # Last 10 activities
            total_time_spent=total_time
        )
    )

@router.post("/", response_model=ResponseModel[ProgressResponse])
async def update_progress(
    update: ProgressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Find existing progress or create new
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.language == update.language,
        UserProgress.region == update.region
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            language=update.language,
            region=update.region,
            proficiency_level=update.score,
            completed_challenges=[update.metadata] if update.metadata else [],
            vocabulary_mastered={},
            last_location="",
            updated_at=datetime.utcnow()
        )
        db.add(progress)
    else:
        # Update existing progress
        progress.proficiency_level = (progress.proficiency_level + update.score) / 2
        if update.metadata:
            # Initialize completed_challenges if None
            if progress.completed_challenges is None:
                progress.completed_challenges = []
            elif not isinstance(progress.completed_challenges, list):
                progress.completed_challenges = []
            
            # Check if challenge already exists
            existing_challenge_ids = [c.get("id") for c in progress.completed_challenges if isinstance(c, dict) and "id" in c]
            if update.metadata.get("id") not in existing_challenge_ids:
                # Create a new list to ensure SQLAlchemy detects the change
                new_challenges = progress.completed_challenges.copy()
                new_challenges.append(update.metadata)
                progress.completed_challenges = new_challenges
                # Flag the JSON field as modified
                flag_modified(progress, "completed_challenges")
        
        # Update timestamp
        progress.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(progress)
    
    # Extract challenge IDs for response
    challenge_ids = [c.get("id") for c in progress.completed_challenges if isinstance(c, dict) and "id" in c]
    
    return ResponseModel(
        success=True,
        message="Progress updated successfully",
        data=ProgressResponse(
            language=progress.language,
            region=progress.region,
            proficiency_level=progress.proficiency_level,
            completed_challenges=challenge_ids,
            achievements=[],  # Will be implemented with achievement system
            last_activity=progress.updated_at or progress.created_at
        )
    )

@router.get("/language/{language}", response_model=ResponseModel[List[ProgressResponse]])
async def get_language_progress(
    language: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.language == language
    ).all()
    
    if not progress:
        return ResponseModel(
            success=True,
            message=f"No progress found for language: {language}",
            data=[]
        )
    
    response_data = [
        ProgressResponse(
            language=p.language,
            region=p.region,
            proficiency_level=p.proficiency_level,
            completed_challenges=[c["id"] for c in p.completed_challenges if "id" in c],
            achievements=[],  # Will be implemented with achievement system
            last_activity=p.created_at if p.updated_at is None else p.updated_at
        ) for p in progress
    ]
    
    return ResponseModel(
        success=True,
        message=f"Progress retrieved for language: {language}",
        data=response_data
    )

@router.get("/region/{region}", response_model=ResponseModel[List[ProgressResponse]])
async def get_region_progress(
    region: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.region == region
    ).all()
    
    if not progress:
        return ResponseModel(
            success=True,
            message=f"No progress found for region: {region}",
            data=[]
        )
    
    response_data = [
        ProgressResponse(
            language=p.language,
            region=p.region,
            proficiency_level=p.proficiency_level,
            completed_challenges=[c["id"] for c in p.completed_challenges if "id" in c],
            achievements=[],  # Will be implemented with achievement system
            last_activity=p.created_at if p.updated_at is None else p.updated_at
        ) for p in progress
    ]
    
    return ResponseModel(
        success=True,
        message=f"Progress retrieved for region: {region}",
        data=response_data
    )

@router.post("/poi/{poi_id}/complete", response_model=ResponseModel[List[Achievement]])
async def complete_poi_content(
    poi_id: str,
    update: POIProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[List[Achievement]]:
    """Record completion of POI content and check for achievements"""
    # Verify POI exists
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")

    # Get or create progress record
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.region == poi.region_id
    ).first()

    if not progress:
        raise HTTPException(status_code=400, detail="No progress record found for this region")

    # Update content mastery
    if update.content_type not in progress.content_mastery:
        progress.content_mastery[update.content_type] = {}
    
    for item_id in update.completed_items:
        progress.content_mastery[update.content_type][item_id] = update.score

    # Update POI progress
    if poi_id not in progress.poi_progress:
        progress.poi_progress[poi_id] = {
            "visits": 1,
            "completed_content": [],
            "total_time": update.time_spent,
            "last_visit": str(datetime.utcnow())
        }
    else:
        poi_progress = progress.poi_progress[poi_id]
        poi_progress["completed_content"].extend(update.completed_items)
        poi_progress["total_time"] = poi_progress.get("total_time", 0) + update.time_spent
        poi_progress["last_visit"] = str(datetime.utcnow())

    # Check for achievements
    new_achievements = []
    
    # Visit count achievements
    visit_count = progress.poi_progress[poi_id].get("visits", 0)
    if visit_count >= 5 and not any(a["id"] == f"poi_visits_{poi_id}_5" for a in progress.achievements):
        new_achievements.append({
            "id": f"poi_visits_{poi_id}_5",
            "name": "Frequent Visitor",
            "description": f"Visited {poi.name} 5 times",
            "type": "poi_visit",
            "progress": 100,
            "completed": True,
            "completed_at": datetime.utcnow(),
            "metadata": {"poi_id": poi_id, "visit_count": visit_count}
        })

    # Content mastery achievements
    completed_count = len(progress.poi_progress[poi_id].get("completed_content", []))
    total_content = len(poi.content_ids)
    if total_content > 0:
        mastery_percent = (completed_count / total_content) * 100
        if mastery_percent >= 50 and not any(a["id"] == f"poi_mastery_{poi_id}_50" for a in progress.achievements):
            new_achievements.append({
                "id": f"poi_mastery_{poi_id}_50",
                "name": "POI Explorer",
                "description": f"Completed 50% of content at {poi.name}",
                "type": "content_mastery",
                "progress": mastery_percent,
                "completed": True,
                "completed_at": datetime.utcnow(),
                "metadata": {"poi_id": poi_id, "mastery_percent": mastery_percent}
            })
        if mastery_percent >= 100 and not any(a["id"] == f"poi_mastery_{poi_id}_100" for a in progress.achievements):
            new_achievements.append({
                "id": f"poi_mastery_{poi_id}_100",
                "name": "POI Master",
                "description": f"Completed all content at {poi.name}",
                "type": "content_mastery",
                "progress": 100,
                "completed": True,
                "completed_at": datetime.utcnow(),
                "metadata": {"poi_id": poi_id, "mastery_percent": mastery_percent}
            })

    # Add new achievements
    progress.achievements.extend(new_achievements)
    
    # Update progress and recalculate proficiency
    content_scores = []
    for content_type, items in progress.content_mastery.items():
        content_scores.extend(items.values())
    
    if content_scores:
        progress.proficiency_level = sum(content_scores) / len(content_scores)

    db.commit()

    # Invalidate cached content for this POI
    await cache.invalidate_poi_content(poi_id)

    return ResponseModel(
        success=True,
        message=f"Content completion recorded for POI: {poi.name}",
        data=[Achievement(**achievement) for achievement in new_achievements]
    )