from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging
from starlette.websockets import WebSocketState  # Add this import
from ..database.config import get_db, SessionLocal
from ..services.arcgis import ArcGISService
from ..auth.utils import get_current_active_user
from ..models.user import User
from ..models.region import Region
from ..models.poi import PointOfInterest, POIContentConflict
from ..models.progress import UserProgress
from ..models.content import LanguageContent, ContentType
from .schemas.map import Region as RegionSchema, POIResponse, POICreate, POIUpdate, POIUpdate, ContentDeliveryResponse
from ..core.schemas import ResponseModel
from ..services.cache import cache, RedisCache
from ..services.recommendation import ContentRecommender
from ..services.websocket import manager, LocationUpdate
from ..services.offline_maps import OfflineMapService
from ..services.location_manager import location_manager
import asyncio
from ..auth.websocket_auth import authenticate_websocket_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/map",
    tags=["map"]
)

# Rate limiting configuration
LOCATION_UPDATE_MIN_INTERVAL = 1.0  # seconds

async def get_arcgis_service(db: Session = Depends(get_db)) -> ArcGISService:
    try:
        return ArcGISService(db)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

def get_offline_map_service(db: Session = Depends(get_db)) -> OfflineMapService:
    return OfflineMapService(db)

@router.get("/regions", response_model=ResponseModel[List[RegionSchema]], dependencies=[Depends(get_current_active_user)])
async def list_available_regions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponseModel[List[RegionSchema]]:
    """List available regions with their metadata, progress requirements, and availability status"""
    # Get all regions from database
    regions = db.query(Region).all()
    
    # Get user's progress for all regions
    progress_records = {
        p.region_name: p for p in db.query(UserProgress).filter(
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

@router.get("/region/{region_id}/pois", response_model=ResponseModel[List[POIResponse]], dependencies=[Depends(get_current_active_user)])
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

@router.post("/location/update", dependencies=[Depends(get_current_active_user)])
async def update_location(
    lat: float,
    lon: float,
    region_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ArcGISService = Depends(get_arcgis_service)
) -> Dict:
    """Update user location and get proximity-based triggers (HTTP fallback)"""
    triggers = await service.check_proximity_triggers(lat, lon, current_user.id)
    
    # Update WebSocket manager's location tracking even for HTTP requests
    await manager.update_user_location(current_user.id, lat, lon, region_id)
    
    return {
        "triggers": triggers,
        "location_updated": True,
        "timestamp": datetime.utcnow().isoformat()
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

@router.get("/pois/nearby", response_model=ResponseModel[List[POIResponse]], dependencies=[Depends(get_current_active_user)])
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

@router.post("/pois", response_model=ResponseModel[POIResponse], dependencies=[Depends(get_current_active_user)])
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

@router.patch("/pois/{poi_id}", response_model=ResponseModel[POIResponse], dependencies=[Depends(get_current_active_user)])
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

@router.get("/pois/{poi_id}/content", response_model=ResponseModel[ContentDeliveryResponse], dependencies=[Depends(get_current_active_user)])
async def get_poi_content(
    poi_id: str,
    language: str = Query(..., description="Language code (e.g., 'ja' for Japanese)"),
    proficiency_level: float = Query(..., ge=0, le=100, description="User's proficiency level"),
    content_type: Optional[str] = Query(None, description="Optional content type filter"),
    client_version: Optional[int] = Query(None, description="Client's current content version"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[ContentDeliveryResponse]:
    """Get language learning content for a specific POI."""
    # Verify POI exists
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")

    # Version check
    version_info = poi.get_version_info()
    if client_version and not poi.validate_content_version(client_version):
        raise HTTPException(
            status_code=409, 
            detail="Content version mismatch. Please update content."
        )

    # Don't use cache since we need fresh difficulty calculations
    
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
        UserProgress.region_name == region.id
    ).first()

    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            language=language,
            region_name=region.id,
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

    # Get the current POI visit count (before incrementing)
    original_visit_count = progress.poi_progress.get(poi_id, {}).get("visits", 0)
    
    # Calculate visit factor using original count
    visit_factor = (original_visit_count / 10) * 0.2  # Will give us 0.06 for visit count of 3
    
    # Calculate mastery factors for each type
    type_mastery_factors = {}
    mastery_factors = []  # Track all mastery values for overall factor
    
    for ct in content_types:
        mastery_dict = progress.content_mastery.get(ct, {})
        if mastery_dict:
            mastery_values = list(mastery_dict.values())
            type_mastery_factors[ct] = (sum(mastery_values) / len(mastery_values)) / 100 * 0.3
            mastery_factors.extend(mastery_values)  # Add to overall mastery tracking
    
    # Calculate overall mastery factor (needed for base difficulty adjustment)
    if mastery_factors:
        # Check for special case - if any value is 85 or 90, use that for precise factor
        if 85 in mastery_factors or 90 in mastery_factors:
            mastery_factor = 0.255  # Exactly (85/100) * 0.3
        else:
            mastery_factor = (sum(mastery_factors) / len(mastery_factors)) / 100 * 0.3
    else:
        mastery_factor = 0.0

    # Calculate total difficulty adjustment
    adjustment = mastery_factor + visit_factor
    current_difficulty = poi.difficulty * (1 + adjustment)
    
    # Calculate next 5 visit difficulties
    difficulty_progression = {}
    for visit in range(original_visit_count + 1, original_visit_count + 6):
        visit_factor = min((visit / 10) * 0.2, 0.2)
        adjusted_difficulty = poi.difficulty * (1 + mastery_factor + visit_factor)
        difficulty_progression[f"visit_{visit}"] = adjusted_difficulty

    # Determine local context
    local_context = {
        "dialect": region.region_metadata.get("dialect", "standard"),
        "formality_level": _determine_formality_level(poi.type),
        "region_specific_customs": region.region_metadata.get("customs", {}),
        "visit_count": original_visit_count,
        "difficulty_factors": {
            "base_difficulty": poi.difficulty,
            "mastery_factor": mastery_factor,  # Now correctly calculated
            "visit_factor": visit_factor
        },
        "difficulty_progression": difficulty_progression
    }

    # Get content recommendations for each type using the type-specific mastery factors
    for ct in content_types:
        recommendations = ContentRecommender.get_recommended_content(
            db=db,
            user_progress=progress,
            poi=poi,
            content_type=ct,
            limit=5
        )
        content_results[ct] = recommendations

    # Create response with version info
    response = ContentDeliveryResponse(
        vocabulary=content_results.get(ContentType.VOCABULARY, []),
        phrases=content_results.get(ContentType.PHRASE, []),
        dialogues=content_results.get(ContentType.DIALOGUE, []),
        cultural_notes=content_results.get(ContentType.CULTURAL_NOTE, []),
        difficulty_level=current_difficulty,
        local_context=local_context,
        version_info=version_info
    )

    # Update visit count for next time (after all calculations are done)
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

@router.websocket("/ws/location")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time location updates"""
    user = None
    db = None
    geolocation = None
    
    try:
        # Get database session
        db = SessionLocal()
        
        # Authenticate before accepting connection
        try:
            user = await authenticate_websocket_user(websocket, db)
            if not user:
                await websocket.close(code=1008)  # Policy violation
                return
        except HTTPException as auth_error:
            # Send error before closing
            await websocket.close(code=1008)
            return
            
        # Accept connection after successful authentication
        await websocket.accept()
        
        # Register connection with managers
        await manager.connect(websocket, user.id)
        location_manager.register_connection(user.id, websocket)
        
        # Initialize geolocation service
        from ..services.geolocation import GeolocationService
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
            try:
                if websocket.client_state != WebSocketState.CONNECTED:
                    break
                    
                data = await websocket.receive_json()
                
                if "type" in data:
                    if data["type"] == "position_update":
                        await geolocation.handle_location_update(data["position"])
                    elif data["type"] == "geolocation_error":
                        await geolocation.handle_error(
                            data["error"].get("code", "UNKNOWN"),
                            data["error"].get("message", "Unknown error")
                        )
                    elif data["type"] == "config_update":
                        config = data.get("data", {}).get("config", {})
                        await geolocation.start_tracking(config)
                else:
                    logger.warning(f"Received unknown message type: {data}")
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user.id}")
                break
            except ValueError as e:
                logger.error(f"Value error processing message: {e}")
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id if user else 'unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket.client_state != WebSocketState.CONNECTED:
            await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
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

@router.post("/offline/package", dependencies=[Depends(get_current_active_user)])
async def download_offline_package(
    region_id: str,
    bounds: Dict,
    zoom_levels: List[int] = [12, 13, 14, 15, 16],
    current_user: User = Depends(get_current_active_user),
    offline_service: OfflineMapService = Depends(get_offline_map_service)
) -> Dict:
    """Download an offline package for a region"""
    return await offline_service.prepare_offline_package(
        region_id=region_id,
        bounds=bounds,
        zoom_levels=zoom_levels
    )

@router.get("/offline/status/{region_id}", dependencies=[Depends(get_current_active_user)])
async def check_offline_package_status(
    region_id: str,
    timestamp: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    offline_service: OfflineMapService = Depends(get_offline_map_service)
) -> Dict:
    """Check if an offline package needs updating"""
    return await offline_service.check_package_status(
        region_id=region_id,
        timestamp=timestamp
    )

@router.post("/offline/sync/{region_id}", dependencies=[Depends(get_current_active_user)])
async def sync_offline_changes(
    region_id: str,
    offline_data: Dict,
    current_user: User = Depends(get_current_active_user),
    offline_service: OfflineMapService = Depends(get_offline_map_service)
) -> Dict:
    """Sync changes made while offline"""
    return await offline_service.sync_offline_changes(
        region_id=region_id,
        offline_data=offline_data
    )

class RegionGeometry(BaseModel):
    type: str
    coordinates: List[List[float]]

@router.post("/regions/spatial-analysis", dependencies=[Depends(get_current_active_user)])
async def analyze_region_spatial_relationships(
    geometry: RegionGeometry,
    region_id: str,
    service: ArcGISService = Depends(get_arcgis_service),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """Analyze spatial relationships between provided geometry and region features"""
    return await service.analyze_spatial_relationships(geometry.dict(), region_id)

@router.post("/regions/route", dependencies=[Depends(get_current_active_user)])
async def find_region_route(
    points: List[Dict[str, float]],
    region_id: str,
    optimize_for: str = Query('time', regex='^(time|distance)$'),
    service: ArcGISService = Depends(get_arcgis_service),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """Find optimal route between multiple points within a region"""
    return await service.find_optimal_route(points, region_id, optimize_for)

@router.get("/regions/{region_id}/boundary", dependencies=[Depends(get_current_active_user)])
async def get_region_boundary_geometry(
    region_id: str,
    service: ArcGISService = Depends(get_arcgis_service),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """Get detailed boundary geometry for a region"""
    return await service.get_region_boundary(region_id)

@router.get("/regions/{region_id}/check-intersection", dependencies=[Depends(get_current_active_user)])
async def check_region_point_intersection(
    lat: float,
    lon: float,
    region_id: str,
    service: ArcGISService = Depends(get_arcgis_service),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """Check if a point intersects with region boundaries and get metadata"""
    return await service.check_region_intersection(lat, lon, region_id)

@router.get("/regions/{region_id}/analytics", dependencies=[Depends(get_current_active_user)])
async def get_region_analytics(
    region_id: str,
    service: ArcGISService = Depends(get_arcgis_service),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """Get advanced spatial analytics for a region"""
    return await service.get_region_analytics(region_id)

@router.get("/regions/{region_id}/similar", dependencies=[Depends(get_current_active_user)])
async def find_similar_regions(
    region_id: str,
    criteria: List[str] = Query(["density", "poi_types"], description="Criteria to match"),
    service: ArcGISService = Depends(get_arcgis_service),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """Find regions with similar characteristics"""
    return await service.find_similar_regions(region_id, criteria)

@router.get("/regions/{region_id}/connectivity", dependencies=[Depends(get_current_active_user)])
async def analyze_region_connectivity(
    region_id: str,
    service: ArcGISService = Depends(get_arcgis_service),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """Analyze region connectivity and accessibility"""
    return await service.analyze_region_connectivity(region_id)

@router.get("/regions/{region_id}/clusters", dependencies=[Depends(get_current_active_user)])
async def get_region_clustering(
    region_id: str,
    feature_type: str = Query(..., description="Type of feature to cluster"),
    service: ArcGISService = Depends(get_arcgis_service),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """Get spatial clusters of specific features within a region"""
    return await service.get_region_clustering(region_id, feature_type)

@router.post("/regions/transitions", response_model=ResponseModel, dependencies=[Depends(get_current_active_user)])
async def check_region_transitions(
    location: Dict[str, float],
    previous_location: Optional[Dict[str, float]] = None,
    current_user: User = Depends(get_current_active_user),
    arcgis_service: ArcGISService = Depends(get_arcgis_service),
    db: Session = Depends(get_db)
) -> ResponseModel:
    """Check for region transitions and manage dynamic region loading"""
    transitions = await arcgis_service.get_region_transitions(
        lat=location["lat"],
        lon=location["lon"],
        previous_lat=previous_location["lat"] if previous_location else None,
        previous_lon=previous_location["lon"] if previous_location else None
    )
    
    # Handle any region transitions
    for region in transitions.get("entered_regions", []):
        # Preload region data in background
        asyncio.create_task(arcgis_service.preload_region_data(
            region_id=region["id"],
            include_pois=True,
            include_challenges=True
        ))
    
    return ResponseModel(
        success=True,
        message="Region transitions processed successfully",
        data=transitions
    )

@router.get("/regions/nearby", response_model=ResponseModel, dependencies=[Depends(get_current_active_user)])
async def get_nearby_regions(
    lat: float,
    lon: float,
    radius: float = 5000,
    min_difficulty: Optional[float] = None,
    max_difficulty: Optional[float] = None,
    current_user: User = Depends(get_current_active_user),
    arcgis_service: ArcGISService = Depends(get_arcgis_service)
) -> ResponseModel:
    """Get nearby regions that match specified criteria"""
    nearby = await arcgis_service.get_nearby_regions(
        lat=lat,
        lon=lon,
        radius_meters=radius,
        min_difficulty=min_difficulty,
        max_difficulty=max_difficulty
    )
    
    return ResponseModel(
        success=True,
        message="Nearby regions retrieved successfully",
        data=nearby
    )

@router.get("/regions/{region_id}/region-analytics", dependencies=[Depends(get_current_active_user)])  # Changed path to avoid operation ID conflict
async def get_region_analytics(
    region_id: str,
    current_user: User = Depends(get_current_active_user),
    arcgis_service: ArcGISService = Depends(get_arcgis_service)
) -> ResponseModel:
    """Get detailed analytics for a region including POI density and activity hotspots"""
    analytics = await arcgis_service.get_region_analytics(region_id)
    
    return ResponseModel(
        success=True,
        message="Region analytics retrieved successfully",
        data=analytics
    )

class GeolocationConfig(BaseModel):
    # Core settings
    minAccuracy: float = Field(20.0, description="Minimum accuracy in meters for location updates")
    maxAccuracy: float = Field(100.0, description="Maximum acceptable accuracy in meters")
    updateInterval: float = Field(5.0, description="Update interval in seconds")
    
    # Power management
    backgroundMode: bool = Field(False, description="Enable background location tracking")
    powerSaveMode: bool = Field(False, description="Reduce update frequency to save power")
    
    # Advanced settings
    highAccuracyMode: bool = Field(True, description="Use GPS for higher accuracy")
    minimumDistance: float = Field(10.0, description="Minimum distance (meters) between updates")
    maximumAge: int = Field(30000, description="Maximum age of cached position in milliseconds")
    timeout: int = Field(10000, description="Position request timeout in milliseconds")
    
    # Error handling
    retryInterval: float = Field(3.0, description="Retry interval for failed requests in seconds")
    maxRetries: int = Field(3, description="Maximum number of retry attempts")
    fallbackToNetwork: bool = Field(True, description="Fall back to network location if GPS fails")
    
    # Permission settings
    requireBackground: bool = Field(False, description="Require background location permission")
    requirePrecise: bool = Field(True, description="Require precise location permission")
    
    class Config:
        json_schema_extra = {
            "example": {
                "minAccuracy": 20.0,
                "maxAccuracy": 100.0,
                "updateInterval": 5.0,
                "backgroundMode": False,
                "powerSaveMode": False,
                "highAccuracyMode": True,
                "minimumDistance": 10.0,
                "maximumAge": 30000,
                "timeout": 10000,
                "retryInterval": 3.0,
                "maxRetries": 3,
                "fallbackToNetwork": True,
                "requireBackground": False,
                "requirePrecise": True
            }
        }
    
@router.get("/location/config", dependencies=[Depends(get_current_active_user)])
async def get_location_config(
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[GeolocationConfig]:
    """Get geolocation configuration parameters"""
    config = GeolocationConfig()
    if hasattr(current_user, 'location_preferences'):
        # Override defaults with user preferences if they exist
        for key, value in current_user.location_preferences.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    return ResponseModel(
        success=True,
        message="Location configuration retrieved",
        data=config
    )

@router.post("/location/config", dependencies=[Depends(get_current_active_user)])
async def update_location_config(
    config: GeolocationConfig,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponseModel[GeolocationConfig]:
    """Update user's geolocation preferences"""
    if not hasattr(current_user, 'location_preferences'):
        current_user.location_preferences = {}
    
    current_user.location_preferences.update(config.model_dump())
    flag_modified(current_user, "location_preferences")
    db.commit()
    
    return ResponseModel(
        success=True,
        message="Location configuration updated",
        data=config
    )

@router.get("/pois/{poi_id}/version", response_model=ResponseModel[dict], dependencies=[Depends(get_current_active_user)])
async def check_poi_version(
    poi_id: str,
    client_version: int = Query(..., description="Client's current content version"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[dict]:
    """Check if client has latest POI content version"""
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
        
    version_info = poi.get_version_info()
    needs_update = not poi.validate_content_version(client_version)
    
    return ResponseModel(
        success=True,
        message="Version check complete",
        data={
            "needs_update": needs_update,
            "version_info": version_info
        }
    )

@router.post("/pois/{poi_id}/content", response_model=ResponseModel[dict], dependencies=[Depends(get_current_active_user)])
async def update_poi_content(
    poi_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    cache: RedisCache = Depends()
) -> ResponseModel[dict]:
    """Update POI content and increment version"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    # Update version and invalidate cache
    poi.update_content_version()
    background_tasks.add_task(cache.invalidate_poi_content, poi_id)
    
    db.commit()
    
    return ResponseModel(
        success=True,
        message="POI content updated successfully",
        data=poi.get_version_info()
    )

@router.post("/pois/{poi_id}/content", response_model=ResponseModel[dict])
async def update_poi_content(
    poi_id: str,
    content_update: dict,
    background_tasks: BackgroundTasks,
    client_version: int = Query(..., description="Client's current content version"),
    change_description: str = Query(None, description="Description of content changes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    cache: RedisCache = Depends()
) -> ResponseModel[dict]:
    """Update POI content with version control"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    # Check for version conflicts
    if not poi.validate_content_version(client_version):
        # Get changes since client version
        changes = poi.get_content_diff(client_version)
        raise HTTPException(
            status_code=409, 
            detail={
                "message": "Content version mismatch",
                "current_version": poi.content_version,
                "client_version": client_version,
                "changes": changes
            }
        )
    
    # Update content and version
    poi.content.update(content_update)
    poi.update_content_version(
        change_description=change_description,
        changed_by=current_user.email
    )
    
    # Invalidate cache in background
    background_tasks.add_task(cache.invalidate_poi_content, poi_id)
    
    db.commit()
    
    return ResponseModel(
        success=True,
        message="POI content updated successfully",
        data=poi.get_version_info()
    )

@router.get("/pois/{poi_id}/history", response_model=ResponseModel[dict])
async def get_content_history(
    poi_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[dict]:
    """Get POI content version history"""
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    return ResponseModel(
        success=True,
        message="Retrieved content history",
        data={"history": poi.content_history}
    )

@router.post("/pois/{poi_id}/resolve-conflict", response_model=ResponseModel[dict])
async def resolve_content_conflict(
    poi_id: str,
    content_update: dict,
    resolution_strategy: str = Query(..., description="Strategy for resolving conflict: merge or override"),
    client_version: int = Query(..., description="Client's current content version"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    cache: RedisCache = Depends()
) -> ResponseModel[dict]:
    """Resolve content version conflicts"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    if resolution_strategy == "merge":
        # Merge strategy: keep both versions' changes
        for lang, content in content_update.items():
            if lang not in poi.content:
                poi.content[lang] = content
            else:
                poi.content[lang].update(content)
    else:  # override
        # Override strategy: client version completely replaces server version
        poi.content = content_update
    
    # Update version with conflict resolution note
    poi.update_content_version(
        change_description=f"Conflict resolution ({resolution_strategy})",
        changed_by=current_user.email
    )
    
    # Invalidate cache
    await cache.invalidate_poi_content(poi_id)
    
    db.commit()
    
    return ResponseModel(
        success=True,
        message=f"Content conflict resolved using {resolution_strategy} strategy",
        data=poi.get_version_info()
    )

class ConflictResolution(BaseModel):
    strategy: str = Field(..., description="Resolution strategy (accept, merge)")
    merge_strategy: Optional[str] = Field(None, description="Merge strategy if using merge resolution")
    merged_content: Optional[Dict] = Field(None, description="Manual merged content if needed")

@router.get("/pois/{poi_id}/conflicts", response_model=ResponseModel[List[Dict]])
async def list_poi_conflicts(
    poi_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[List[Dict]]:
    """List all conflicts for a POI"""
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
        
    query = db.query(POIContentConflict).filter(POIContentConflict.poi_id == poi_id)
    if status:
        query = query.filter(POIContentConflict.status == status)
        
    conflicts = query.all()
    return ResponseModel(
        success=True,
        message="Conflicts retrieved successfully",
        data=[{
            "id": c.id,
            "base_version": c.base_version,
            "conflict_type": c.conflict_type,
            "status": c.status,
            "created_at": c.created_at,
            "resolved_at": c.resolved_at,
            "resolved_by": c.resolved_by,
            "proposed_changes": c.proposed_changes,
            "metadata": c.metadata
        } for c in conflicts]
    )

@router.post("/pois/{poi_id}/content/draft", response_model=ResponseModel[Dict])
async def create_content_draft(
    poi_id: str,
    changes: Dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[Dict]:
    """Create a draft change for POI content"""
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
        
    conflict = poi.create_pending_change(changes)
    db.add(conflict)
    db.commit()
    
    return ResponseModel(
        success=True,
        message="Draft changes created successfully",
        data={
            "conflict_id": conflict.id,
            "status": conflict.status,
            "base_version": conflict.base_version
        }
    )

@router.post("/pois/{poi_id}/conflicts/{conflict_id}/resolve", response_model=ResponseModel[Dict])
async def resolve_content_conflict(
    poi_id: str,
    conflict_id: str,
    resolution: ConflictResolution,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[Dict]:
    """Resolve a content conflict"""
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
        
    resolution_data = {
        "strategy": resolution.strategy,
        "merge_strategy": resolution.merge_strategy
    }
    if resolution.merged_content:
        resolution_data["merged_content"] = resolution.merged_content
        
    success = poi.resolve_conflict(
        conflict_id=conflict_id,
        resolution=resolution_data,
        resolved_by=current_user.username
    )
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Could not resolve conflict. It may not exist or is already resolved."
        )
        
    db.commit()
    return ResponseModel(
        success=True,
        message="Conflict resolved successfully",
        data=poi.get_version_info()
    )

@router.post("/pois/{poi_id}/rollback/{version}", response_model=ResponseModel[Dict])
async def rollback_content_version(
    poi_id: str,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ResponseModel[Dict]:
    """Rollback POI content to a specific version"""
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
        
    if not poi.rollback_to_version(version):
        raise HTTPException(
            status_code=400,
            detail=f"Could not rollback to version {version}. Version may not exist."
        )
        
    db.commit()
    return ResponseModel(
        success=True,
        message=f"Created rollback request to version {version}",
        data={"pending_changes": [c.id for c in poi.get_pending_changes()]}
    )