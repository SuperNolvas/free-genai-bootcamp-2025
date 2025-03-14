from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import Dict, List, Optional
from datetime import datetime
from ..database.config import get_db
from ..services.arcgis import ArcGISService
from ..auth.utils import get_current_active_user
from ..models.user import User
from ..models.region import Region
from ..models.poi import PointOfInterest
from ..models.progress import UserProgress
from ..models.content import LanguageContent, ContentType
from .schemas.map import Region as RegionSchema, POIResponse, POICreate, POIUpdate, ContentDeliveryResponse
from ..core.schemas import ResponseModel
from ..services.cache import cache
from ..services.recommendation import ContentRecommender

router = APIRouter(
    prefix="/map",
    tags=["map"],
    dependencies=[Depends(get_current_active_user)]
)

async def get_arcgis_service(db: Session = Depends(get_db)) -> ArcGISService:
    try:
        return ArcGISService(db)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/regions", response_model=ResponseModel[List[RegionSchema]])
async def list_available_regions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponseModel[List[RegionSchema]]:
    """List available regions with their metadata, progress requirements, and availability status"""
    # Get all regions from database
    regions = db.query(Region).all()
    
    # Get user's progress for all regions
    progress_records = {
        p.region: p for p in db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id
        ).all()
    }
    
    # Convert to response schema with availability checks
    region_responses = []
    for region in regions:
        # Check if user meets requirements
        is_available = True
        requirements = {}
        
        if region.requirements:
            is_available = False
            for req_region, req_level in region.requirements.items():
                if req_region in progress_records:
                    prog = progress_records[req_region]
                    if prog.proficiency_level >= req_level:
                        is_available = True
                        break  # If any requirement is met, region is available
                    else:
                        requirements[req_region] = req_level
                else:
                    requirements[req_region] = req_level
        
        # Convert to response model
        region_response = RegionSchema(
            id=region.id,
            name=region.name,
            local_name=region.local_name,
            description=region.description,
            languages=region.languages,
            bounds=region.bounds,
            center=region.center,
            difficulty_level=region.difficulty_level,
            is_available=is_available,
            requirements=requirements if not is_available else None,
            total_pois=region.total_pois,
            total_challenges=region.total_challenges,
            recommended_level=region.recommended_level,
            created_at=region.created_at,
            updated_at=region.updated_at
        )
        region_responses.append(region_response)
    
    return ResponseModel(
        success=True,
        message="Regions retrieved successfully",
        data=region_responses
    )

@router.get("/region/{region_id}/pois", response_model=ResponseModel[List[POIResponse]])
async def get_region_pois(
    region_id: str,
    poi_type: str = Query(None, description="Type of POI to filter by"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[List[POIResponse]]:
    """Get points of interest for a specific region, with optional type filtering"""
    # Verify region exists and is accessible
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    # Build query
    query = db.query(PointOfInterest).filter(PointOfInterest.region_id == region_id)
    if poi_type:
        query = query.filter(PointOfInterest.poi_type == poi_type)
    
    pois = query.all()
    return ResponseModel(
        success=True,
        message=f"Retrieved {len(pois)} POIs for region {region_id}",
        data=pois
    )

@router.get("/location/search")
async def search_location(
    query: str,
    service: ArcGISService = Depends(get_arcgis_service)
) -> Dict:
    """Search for a location using geocoding, with credit-aware caching"""
    return await service.geocode_location(query)

@router.get("/route")
async def get_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    service: ArcGISService = Depends(get_arcgis_service)
) -> Dict:
    """Get a route between two points, with credit-aware caching"""
    start_point = {"lat": start_lat, "lon": start_lon}
    end_point = {"lat": end_lat, "lon": end_lon}
    return await service.get_route(start_point, end_point)

@router.post("/location/update")
async def update_location(
    lat: float,
    lon: float,
    current_user: User = Depends(get_current_active_user),
    service: ArcGISService = Depends(get_arcgis_service)
) -> Dict:
    """Update user location and get proximity-based triggers"""
    triggers = await service.check_proximity_triggers(lat, lon, current_user.id)
    return {
        "triggers": triggers,
        "location_updated": True
    }

@router.get("/geofence/check")
async def check_geofence(
    lat: float,
    lon: float,
    geofence_id: str,
    service: ArcGISService = Depends(get_arcgis_service)
) -> Dict:
    """Check if a point is within a specific geofence"""
    is_inside = await service.check_point_in_geofence(lat, lon, geofence_id)
    return {
        "geofence_id": geofence_id,
        "is_inside": is_inside
    }

@router.get("/region/{region_id}/layers")
async def get_map_layers(
    region_id: str,
    service: ArcGISService = Depends(get_arcgis_service)
) -> Dict:
    """Get available map layers for a region"""
    return await service.get_region_layers(region_id)

@router.get("/pois/nearby", response_model=ResponseModel[List[POIResponse]])
async def get_nearby_points_of_interest(
    lat: float,
    lon: float,
    radius: float = Query(1000, description="Search radius in meters"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: ArcGISService = Depends(get_arcgis_service)
) -> ResponseModel[List[POIResponse]]:
    """Get POIs within specified radius of a point"""
    # Use ArcGIS to find POIs within radius
    nearby = await service.get_nearby_pois(lat, lon, radius)
    
    # Get POI IDs from ArcGIS response
    poi_ids = [feature["id"] for feature in nearby.get("features", [])]
    
    # Fetch full POI details from database
    pois = db.query(PointOfInterest).filter(PointOfInterest.id.in_(poi_ids)).all()
    
    return ResponseModel(
        success=True,
        message=f"Found {len(pois)} POIs within {radius}m",
        data=pois
    )

@router.post("/pois", response_model=ResponseModel[POIResponse])
async def create_poi(
    poi: POICreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: ArcGISService = Depends(get_arcgis_service)
) -> ResponseModel[POIResponse]:
    """Create a new POI. Admin only."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to create POIs")
    
    # Verify region exists
    region = db.query(Region).filter(Region.id == poi.region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    # Create POI
    db_poi = PointOfInterest(**poi.model_dump(exclude_unset=True))
    db.add(db_poi)
    db.commit()
    db.refresh(db_poi)
    
    # Update region POI count
    region.total_pois += 1
    db.commit()
    
    return ResponseModel(
        success=True,
        message="POI created successfully",
        data=db_poi
    )

@router.patch("/pois/{poi_id}", response_model=ResponseModel[POIResponse])
async def update_poi(
    poi_id: str,
    poi_update: POIUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[POIResponse]:
    """Update a POI. Admin only."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update POIs")
    
    db_poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not db_poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    # Update POI fields
    for field, value in poi_update.model_dump(exclude_unset=True).items():
        setattr(db_poi, field, value)
    
    db.commit()
    db.refresh(db_poi)
    
    return ResponseModel(
        success=True,
        message="POI updated successfully",
        data=db_poi
    )

@router.get("/pois/{poi_id}/content", response_model=ResponseModel[ContentDeliveryResponse])
async def get_poi_content(
    poi_id: str,
    language: str = Query(..., description="Language code (e.g., 'ja' for Japanese)"),
    proficiency_level: float = Query(..., ge=0, le=100, description="User's proficiency level"),
    content_type: Optional[str] = Query(None, description="Optional content type filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[ContentDeliveryResponse]:
    """Get language learning content for a specific POI."""
    # Try to get from cache first
    cached_content = await cache.get_poi_content(poi_id, language, proficiency_level)
    if cached_content:
        return ResponseModel(
            success=True,
            message=f"Retrieved cached content for POI: {poi_id}",
            data=ContentDeliveryResponse(**cached_content)
        )

    # Verify POI exists
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")

    # Get region for dialect/context information
    region = db.query(Region).filter(Region.id == poi.region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    # Get or initialize user progress
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.language == language,
        UserProgress.region == region.id
    ).first()

    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            language=language,
            region=region.id,
            proficiency_level=proficiency_level,
            poi_progress={},
            content_mastery={},
            achievements=[]
        )
        db.add(progress)
        db.commit()

    # Get recommended content for each type
    content_results = {}
    content_types = [content_type] if content_type else [
        ContentType.VOCABULARY,
        ContentType.PHRASE,
        ContentType.DIALOGUE,
        ContentType.CULTURAL_NOTE
    ]

    for ct in content_types:
        recommendations = ContentRecommender.get_recommended_content(
            db=db,
            user_progress=progress,
            poi=poi,
            content_type=ct,
            limit=5
        )
        content_results[ct] = [
            {
                **content,
                "completed": content["id"] in progress.content_mastery.get(ct, {}),
                "mastery_level": progress.content_mastery.get(ct, {}).get(content["id"], 0)
            }
            for content in recommendations
        ]

    # Calculate visit-based metrics and overall mastery
    visit_count = progress.poi_progress.get(poi_id, {}).get("visits", 0)
    
    # Calculate average mastery from all mastered content
    all_mastery = []
    for ct, mastery_dict in progress.content_mastery.items():
        all_mastery.extend(mastery_dict.values())
    avg_mastery = sum(all_mastery) / len(all_mastery) if all_mastery else 0

    # Calculate current difficulty and factors using POI difficulty as base
    current_difficulty = ContentRecommender.calculate_content_difficulty(
        poi.difficulty_level,  # Use POI difficulty as base
        avg_mastery,
        visit_count
    )

    # Calculate difficulty factors
    difficulty_factors = {
        "base_difficulty": poi.difficulty_level,
        "mastery_factor": (avg_mastery / 100) * 0.3 if all_mastery else 0,  # Added check for empty mastery
        "visit_factor": min((visit_count / 10) * 0.2, 0.2)
    }

    # Project future difficulty progression
    difficulty_progression = {}
    for future_visit in range(visit_count + 1, visit_count + 6):
        projected_difficulty = ContentRecommender.calculate_content_difficulty(
            poi.difficulty_level,
            avg_mastery,
            future_visit
        )
        difficulty_progression[f"visit_{future_visit}"] = projected_difficulty

    # Determine local context with enhanced difficulty info
    local_context = {
        "dialect": region.metadata.get("dialect", "standard"),  # Fixed: using region.metadata instead of region.region_metadata
        "formality_level": _determine_formality_level(poi.poi_type),
        "region_specific_customs": region.metadata.get("customs", {}),  # Fixed: using region.metadata here too
        "visit_count": visit_count,
        "difficulty_factors": difficulty_factors,
        "difficulty_progression": difficulty_progression
    }

    # Create response
    response = ContentDeliveryResponse(
        vocabulary=content_results.get(ContentType.VOCABULARY, []),
        phrases=content_results.get(ContentType.PHRASE, []),
        dialogues=content_results.get(ContentType.DIALOGUE, []),
        cultural_notes=content_results.get(ContentType.CULTURAL_NOTE, []),
        difficulty_level=current_difficulty,
        local_context=local_context
    )

    # Cache the response
    await cache.set_poi_content(poi_id, language, proficiency_level, response.model_dump())

    # Update POI visit count
    if not progress.poi_progress.get(poi_id):
        progress.poi_progress[poi_id] = {
            "visits": 1,
            "completed_content": [],
            "total_time": 0,
            "last_visit": str(datetime.utcnow())
        }
    else:
        progress.poi_progress[poi_id]["visits"] += 1
        progress.poi_progress[poi_id]["last_visit"] = str(datetime.utcnow())
    
    flag_modified(progress, "poi_progress")
    db.commit()

    return ResponseModel(
        success=True,
        message=f"Retrieved learning content for POI: {poi.name}",
        data=response
    )

def _determine_formality_level(poi_type: str) -> str:
    """Determine appropriate formality level based on POI type."""
    formal_types = {"temple", "shrine", "government_office", "museum"}
    casual_types = {"park", "shopping_street", "market"}
    
    if poi_type in formal_types:
        return "formal"
    elif poi_type in casual_types:
        return "casual"
    return "neutral"