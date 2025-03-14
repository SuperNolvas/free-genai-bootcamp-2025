from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List
from ..database.config import get_db
from ..services.arcgis import ArcGISService
from ..auth.utils import get_current_active_user
from ..models.user import User
from ..models.region import Region
from ..models.progress import UserProgress
from .schemas.map import Region as RegionSchema
from ..core.schemas import ResponseModel

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

@router.get("/region/{region_id}/pois")
async def get_region_pois(
    region_id: str,
    poi_type: str = Query(None, description="Type of POI to filter by"),
    service: ArcGISService = Depends(get_arcgis_service)
) -> Dict:
    """Get points of interest for a specific region, with optional type filtering"""
    params = {"region": region_id}
    if poi_type:
        params["type"] = poi_type
    return await service.get_map_features(region_id, "poi")

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

@router.get("/pois/nearby")
async def get_nearby_points_of_interest(
    lat: float,
    lon: float,
    radius: float = Query(1000, description="Search radius in meters"),
    service: ArcGISService = Depends(get_arcgis_service)
) -> Dict:
    """Get POIs within specified radius of a point"""
    return await service.get_nearby_pois(lat, lon, radius)