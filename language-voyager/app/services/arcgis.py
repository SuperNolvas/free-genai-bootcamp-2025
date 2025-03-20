from fastapi import HTTPException
from sqlalchemy.orm import Session
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import redis
import hashlib
import math
from ..core.config import get_settings
from ..models.arcgis_usage import ArcGISUsage

settings = get_settings()
redis_client = redis.from_url(settings.REDIS_URL)
logger = logging.getLogger(__name__)

class ArcGISCredit:
    # Credit costs per operation (based on ArcGIS documentation)
    CREDIT_COSTS = {
        'geocoding': 0.04,
        'routing': 0.005,
        'tile_request': 0.001,
        'feature_request': 0.002,
        'place_search': 0.04,
        'place_details': 0.04,
        'elevation': 0.001
    }

class ArcGISService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()  # Store settings instance
        self.api_key = self.settings.ARCGIS_API_KEY
        if not self.api_key:
            raise ValueError("ArcGIS API key is not configured")

    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate a unique cache key for a request"""
        # Sort params to ensure consistent key generation
        param_str = json.dumps(params, sort_keys=True)
        # Create hash of endpoint and parameters
        return f"arcgis:{endpoint}:{hashlib.sha256(param_str.encode()).hexdigest()}"

    async def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if available"""
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in cache for key {cache_key}")
                redis_client.delete(cache_key)
        return None

    async def _cache_response(self, cache_key: str, response: Dict, ttl: int = None):
        """Cache response with expiration"""
        if ttl is None:
            ttl = settings.ARCGIS_CACHE_DURATION
        try:
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(response)
            )
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to cache response: {str(e)}")

    async def _check_usage_limits(self, operation_type: str) -> Tuple[bool, float, str]:
        """Check both monthly operation limits and daily credit limits"""
        # First check monthly operation limit
        within_limit, usage_percentage, alert_level = ArcGISUsage.check_monthly_limit(
            self.db, operation_type
        )
        
        if not within_limit:
            raise HTTPException(
                status_code=429,
                detail=f"Monthly limit for {operation_type} operations reached. Please try again next month."
            )

        # Then check daily credit limit
        current_usage = ArcGISUsage.get_daily_usage(self.db)
        operation_cost = ArcGISCredit.CREDIT_COSTS.get(operation_type, 0.04)
        if current_usage + operation_cost > self.settings.ARCGIS_MAX_CREDITS_PER_DAY:
            raise HTTPException(
                status_code=429,
                detail="Daily ArcGIS credit limit reached. Please try again tomorrow."
            )

        # Log alerts based on threshold
        if alert_level:
            logger.warning(
                f"ArcGIS {operation_type} usage alert: {alert_level.upper()} - "
                f"{usage_percentage:.1f}% of monthly limit"
            )
            # Cache the alert to prevent spam
            alert_key = f"arcgis:alert:{operation_type}:{datetime.now().strftime('%Y-%m')}"
            if not redis_client.exists(alert_key):
                redis_client.setex(alert_key, 86400, json.dumps({
                    'level': alert_level,
                    'percentage': usage_percentage
                }))

        return within_limit, usage_percentage, alert_level

    def _log_usage(self, operation_type: str, cached: bool = False, request_path: str = None):
        """Log credit usage to database"""
        usage = ArcGISUsage(
            operation_type=operation_type,
            credits_used=ArcGISCredit.CREDIT_COSTS.get(operation_type, 0.04),
            cached=cached,
            request_path=request_path
        )
        self.db.add(usage)
        self.db.commit()

    async def _make_request(self, endpoint: str, params: Dict[str, Any], operation_type: str) -> Dict:
        """Make an ArcGIS API request with credit and quota management"""
        # Generate cache key
        cache_key = self._generate_cache_key(endpoint, params)
        
        # Check cache first
        cached_response = await self._get_cached_response(cache_key)
        if cached_response:
            self._log_usage(operation_type, cached=True, request_path=endpoint)
            return cached_response

        # Check usage limits
        within_limit, usage_percentage, alert_level = await self._check_usage_limits(operation_type)

        # Make request
        base_url = "https://geocode-api.arcgis.com/arcgis/rest/services/World/GeocodeServer" if operation_type == "geocoding" else "https://www.arcgis.com/sharing/rest"
        
        params['token'] = self.api_key
        session = aiohttp.ClientSession()
        try:
            url = f"{base_url}/{endpoint}"
            response = await session.get(url, params=params)
            if response.status != 200:
                raise HTTPException(
                    status_code=response.status,
                    detail=f"ArcGIS API request failed: {url}"
                )
            result = await response.json()
        finally:
            await session.close()

        # Log credit usage and cache response
        self._log_usage(operation_type)
        await self._cache_response(cache_key, result)

        return result

    async def get_map_features(self, region: str, feature_type: str) -> Dict:
        """Get map features for a region with credit-aware caching"""
        params = {
            'f': 'json',
            'region': region,
            'type': feature_type,
            'maxFeatures': settings.ARCGIS_FEATURE_LIMIT
        }
        return await self._make_request('features', params, 'feature_request')

    async def geocode_location(self, address: str) -> Dict:
        """Geocode an address with credit-aware caching"""
        params = {
            'f': 'json',
            'address': address,
            'outFields': '*',
            'singleLine': address
        }
        return await self._make_request('findAddressCandidates', params, 'geocoding')

    async def get_route(self, start_point: Dict[str, float], end_point: Dict[str, float]) -> Dict:
        """Get route between two points with credit-aware caching"""
        params = {
            'f': 'json',
            'stops': f"{start_point['lon']},{start_point['lat']};{end_point['lon']},{end_point['lat']}"
        }
        return await self._make_request('route', params, 'routing')

    async def check_point_in_geofence(self, lat: float, lon: float, geofence_id: str) -> bool:
        """Check if a point is within a geofence boundary"""
        params = {
            'f': 'json',
            'geometry': f"{lon},{lat}",
            'geofenceId': geofence_id
        }
        result = await self._make_request('geofences/contains', params, 'feature_request')
        return result.get('contains', False)

    async def get_nearby_pois(self, lat: float, lon: float, radius_meters: float = 1000) -> Dict:
        """Get POIs within a radius of a point"""
        params = {
            'f': 'json',
            'location': f"{lon},{lat}",
            'radius': radius_meters,
            'maxFeatures': settings.ARCGIS_FEATURE_LIMIT
        }
        return await self._make_request('pois/nearby', params, 'feature_request')

    async def get_region_layers(self, region_id: str) -> Dict:
        """Get available map layers for a region"""
        params = {
            'f': 'json',
            'region': region_id
        }
        return await self._make_request('layers', params, 'feature_request')

    async def check_proximity_triggers(self, lat: float, lon: float, user_id: int) -> List[Dict]:
        """Check for proximity-based triggers (POIs, challenges, etc.)"""
        # First get nearby POIs
        nearby = await self.get_nearby_pois(lat, lon)
        
        # Get cached user location to avoid triggering the same POI multiple times
        cache_key = f"user_location:{user_id}"
        last_location = await self._get_cached_response(cache_key)
        
        triggers = []
        for poi in nearby.get('features', []):
            poi_id = poi.get('id')
            # Check if this POI was already triggered recently
            if not last_location or poi_id not in last_location.get('triggered_pois', []):
                triggers.append({
                    'type': 'poi_proximity',
                    'poi': poi,
                    'distance': poi.get('distance')
                })
        
        # Cache current location and triggered POIs
        await self._cache_response(cache_key, {
            'lat': lat,
            'lon': lon,
            'triggered_pois': [t['poi']['id'] for t in triggers],
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return triggers

    async def analyze_spatial_relationships(self, geometry: Dict, region_id: str) -> Dict:
        """Analyze spatial relationships between a geometry and region features"""
        params = {
            'f': 'json',
            'geometry': json.dumps(geometry),
            'region': region_id,
            'relations': 'intersects,contains,within',
            'returnZ': 'false',
            'returnM': 'false'
        }
        return await self._make_request('geometry/relation', params, 'feature_request')

    async def find_optimal_route(
        self,
        points: List[Dict[str, float]],
        region_id: str,
        optimize_for: str = 'time'
    ) -> Dict:
        """Find optimal route between multiple points within a region
        
        Args:
            points: List of points in format [{"lat": float, "lon": float}, ...]
            region_id: Region to constrain route within
            optimize_for: 'time' or 'distance'
        """
        stops = ';'.join([f"{p['lon']},{p['lat']}" for p in points])
        params = {
            'f': 'json',
            'stops': stops,
            'region': region_id,
            'optimize': optimize_for,
            'restrictionAttributes': 'oneway,private',
            'returnDirections': 'true',
            'returnRoutes': 'true',
            'returnStops': 'true',
            'returnBarriers': 'false',
            'returnPolygonBarriers': 'false',
            'returnPolylineBarriers': 'false',
            'directionsLanguage': 'en'
        }
        return await self._make_request('route/solve', params, 'routing')

    async def get_region_boundary(self, region_id: str) -> Dict:
        """Get detailed boundary geometry for a region"""
        params = {
            'f': 'json',
            'region': region_id,
            'returnGeometry': 'true',
            'geometryPrecision': 6
        }
        return await self._make_request('regions/boundary', params, 'feature_request')

    async def check_region_intersection(self, lat: float, lon: float, region_id: str) -> Dict:
        """Check if a point intersects with region boundaries and get relevant metadata
        
        Returns details about the intersection including:
        - Whether point is in region
        - Distance to region boundary
        - Nearest POIs
        - Sub-region information (if applicable)
        """
        params = {
            'f': 'json',
            'location': f"{lon},{lat}",
            'region': region_id,
            'returnSubRegions': 'true',
            'returnDistance': 'true',
            'returnNearestPOI': 'true'
        }
        return await self._make_request('regions/contains', params, 'feature_request')

    async def get_region_analytics(self, region_id: str) -> Dict:
        """Get advanced spatial analytics for a region including density, clustering, and patterns"""
        params = {
            'f': 'json',
            'region': region_id,
            'analyses': 'density,clusters,patterns',
            'returnStatistics': 'true'
        }
        return await self._make_request('regions/analyze', params, 'feature_request')

    async def find_similar_regions(self, region_id: str, criteria: List[str]) -> Dict:
        """Find regions with similar spatial characteristics
        
        Args:
            region_id: Source region to compare against
            criteria: List of criteria to match (e.g., ['density', 'poi_types', 'area'])
        """
        params = {
            'f': 'json',
            'sourceRegion': region_id,
            'criteria': ','.join(criteria),
            'maxResults': 5
        }
        return await self._make_request('regions/similar', params, 'feature_request')

    async def analyze_region_connectivity(self, region_id: str) -> Dict:
        """Analyze region connectivity including transport links and accessibility"""
        params = {
            'f': 'json',
            'region': region_id,
            'analyzeTransport': 'true',
            'analyzeAccessibility': 'true'
        }
        return await self._make_request('regions/connectivity', params, 'feature_request')

    async def get_region_clustering(self, region_id: str, feature_type: str) -> Dict:
        """Get spatial clusters of specific features within a region
        
        Args:
            region_id: Region to analyze
            feature_type: Type of feature to cluster (e.g., 'poi', 'language_usage')
        """
        params = {
            'f': 'json',
            'region': region_id,
            'featureType': feature_type,
            'method': 'DBSCAN',
            'returnDensity': 'true'
        }
        return await self._make_request('regions/clusters', params, 'feature_request')

    async def find_route_in_region(
        self, 
        points: List[Dict[str, float]], 
        region_id: str,
        prefer_walking: bool = True,
        avoid_tolls: bool = True
    ) -> Dict:
        """Find an optimized route within a region that stays within region boundaries

        Args:
            points: List of waypoints in format [{"lat": float, "lon": float}, ...]
            region_id: Region to constrain route within
            prefer_walking: Whether to optimize for walking paths
            avoid_tolls: Whether to avoid toll roads
        """
        stops = ';'.join([f"{p['lon']},{p['lat']}" for p in points])
        params = {
            'f': 'json',
            'stops': stops,
            'region': region_id,
            'travelMode': 'walking' if prefer_walking else 'driving',
            'directionsLanguage': 'en',
            'returnRoutes': 'true',
            'returnDirections': 'true',
            'returnGeometry': 'true',
            'restrictionAttributes': 'none' if not avoid_tolls else 'tollways',
            'useTraffic': 'false',
            'preserveLastStop': 'true',
            'returnStops': 'true',
            'boundingRegion': region_id  # Ensures route stays in region
        }
        return await self._make_request('route/solve', params, 'routing')

    async def analyze_region_topology(self, region_id: str) -> Dict:
        """Analyze region topology including elevation, slope, and terrain features"""
        params = {
            'f': 'json',
            'region': region_id,
            'returnElevation': 'true',
            'returnSlope': 'true',
            'returnAspect': 'true',
            'returnTerrainFeatures': 'true'
        }
        return await self._make_request('regions/topology', params, 'feature_request')

    async def get_region_poi_density(self, region_id: str, poi_type: Optional[str] = None) -> Dict:
        """Get POI density analysis for a region with optional type filtering"""
        params = {
            'f': 'json',
            'region': region_id,
            'analysisType': 'density',
            'poiType': poi_type,
            'returnHeatmap': 'true',
            'cellSize': 100  # meters
        }
        return await self._make_request('regions/analyze', params, 'feature_request')

    async def find_region_hotspots(
        self,
        region_id: str,
        feature_type: str = 'language_usage',
        min_points: int = 10,
        max_radius: float = 1000
    ) -> Dict:
        """Find activity hotspots within a region using DBSCAN clustering

        Args:
            region_id: Region to analyze
            feature_type: Type of feature to cluster (e.g., 'language_usage', 'user_activity')
            min_points: Minimum points to form a cluster
            max_radius: Maximum radius (meters) to search for cluster points
        """
        params = {
            'f': 'json',
            'region': region_id,
            'featureType': feature_type,
            'analysisType': 'clustering',
            'method': 'DBSCAN',
            'minPoints': min_points,
            'searchRadius': max_radius,
            'returnDensity': 'true',
            'returnClusters': 'true'
        }
        return await self._make_request('regions/analyze', params, 'feature_request')

    async def get_regions_at_location(
        self,
        lat: float,
        lon: float,
        include_metadata: bool = True,
        max_results: int = 5
    ) -> Dict:
        """Get all regions that contain a given point, ordered by area (smallest first)
        
        This helps identify the most specific region when a point intersects multiple regions.
        For example, a point might be in both "Tokyo" and "Asakusa" regions.
        """
        params = {
            'f': 'json',
            'location': f"{lon},{lat}",
            'returnRegions': 'true',
            'returnMetadata': str(include_metadata).lower(),
            'maxResults': max_results,
            'orderBy': 'area',
            'orderDirection': 'asc'
        }
        return await self._make_request('regions/atLocation', params, 'feature_request')

    async def get_region_transitions(
        self,
        lat: float,
        lon: float,
        previous_lat: Optional[float] = None,
        previous_lon: Optional[float] = None
    ) -> Dict:
        """Check if user has transitioned between regions and get transition metadata
        
        Returns:
        - Regions exited since last position
        - Regions entered since last position
        - Current regions (ordered by specificity)
        - Transition events (e.g., "entered_new_region", "exited_region")
        """
        if previous_lat is None or previous_lon is None:
            # First position update, just get current regions
            return await self.get_regions_at_location(lat, lon)

        params = {
            'f': 'json',
            'currentLocation': f"{lon},{lat}",
            'previousLocation': f"{previous_lon},{previous_lat}",
            'returnTransitions': 'true',
            'returnMetadata': 'true'
        }
        return await self._make_request('regions/checkTransitions', params, 'feature_request')

    async def get_nearby_regions(
        self,
        lat: float,
        lon: float,
        radius_meters: float = 5000,
        min_difficulty: Optional[float] = None,
        max_difficulty: Optional[float] = None
    ) -> Dict:
        """Get regions within specified radius that match difficulty criteria"""
        params = {
            'f': 'json',
            'location': f"{lon},{lat}",
            'radius': radius_meters,
            'returnMetadata': 'true',
            'orderBy': 'distance'
        }
        if min_difficulty is not None:
            params['minDifficulty'] = min_difficulty
        if max_difficulty is not None:
            params['maxDifficulty'] = max_difficulty
        
        return await self._make_request('regions/nearby', params, 'feature_request')

    async def preload_region_data(
        self,
        region_id: str,
        include_pois: bool = True,
        include_challenges: bool = True
    ) -> Dict:
        """Preload region data for caching, including POIs and challenges if specified"""
        params = {
            'f': 'json',
            'region': region_id,
            'includePOIs': str(include_pois).lower(),
            'includeChallenges': str(include_challenges).lower(),
            'returnMetadata': 'true'
        }
        return await self._make_request('regions/preload', params, 'feature_request')

    async def generate_tile_package(
        self,
        bounds: Dict[str, float],
        zoom_levels: List[int]
    ) -> Dict:
        """
        Generate a tile package for offline use within specified bounds
        Args:
            bounds: Dict with minx, miny, maxx, maxy in WGS84
            zoom_levels: List of zoom levels to include
        Returns:
            Dict containing tile package info and URLs
        """
        if not self.api_key:
            raise ValueError("ArcGIS API key not configured")
            
        # Calculate tile coordinates for each zoom level
        tile_info = {}
        for zoom in zoom_levels:
            tiles = self._calculate_tiles_for_bounds(bounds, zoom)
            tile_info[str(zoom)] = tiles
            
        # Track credit usage - each tile costs 0.003 credits
        total_tiles = sum(len(tiles['x']) * len(tiles['y']) for tiles in tile_info.values())
        credits_used = total_tiles * 0.003
        
        # Record usage
        usage = ArcGISUsage(
            operation_type="tile_package",
            credits_used=credits_used,
            timestamp=datetime.utcnow()
        )
        self.db.add(usage)
        self.db.commit()
        
        # Generate URLs for each tile
        tile_urls = {}
        for zoom, tiles in tile_info.items():
            tile_urls[zoom] = []
            for x in tiles['x']:
                for y in tiles['y']:
                    url = f"https://basemaps.arcgis.com/arcgis/rest/services/World_Basemap/tile/{zoom}/{y}/{x}?token={self.api_key}"
                    tile_urls[zoom].append({
                        'url': url,
                        'x': x,
                        'y': y,
                        'z': zoom
                    })
                    
        return {
            'bounds': bounds,
            'zoom_levels': zoom_levels,
            'total_tiles': total_tiles,
            'credits_used': credits_used,
            'tiles': tile_urls,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    def _calculate_tiles_for_bounds(
        self,
        bounds: Dict[str, float],
        zoom: int
    ) -> Dict[str, List[int]]:
        """Calculate tile coordinates that cover the given bounds at specified zoom level"""
        def lat_to_y(lat: float, zoom: int) -> int:
            lat_rad = math.radians(lat)
            n = 2.0 ** zoom
            y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
            return y
            
        def lon_to_x(lon: float, zoom: int) -> int:
            n = 2.0 ** zoom
            x = int((lon + 180.0) / 360.0 * n)
            return x
            
        min_x = lon_to_x(bounds['minx'], zoom)
        max_x = lon_to_x(bounds['maxx'], zoom)
        min_y = lat_to_y(bounds['maxy'], zoom)  # Note: y is inverted
        max_y = lat_to_y(bounds['miny'], zoom)
        
        return {
            'x': list(range(min_x, max_x + 1)),
            'y': list(range(min_y, max_y + 1))
        }

    async def reverse_geocode_location(self, lat: float, lon: float) -> Dict:
        """Get detailed location information including street names and water bodies
        
        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            
        Returns:
            Dict containing address and location features (streets, water bodies, etc.)
        """
        params = {
            'f': 'json',
            'location': f"{lon},{lat}",
            'featureTypes': 'StreetAddress,PointAddress,WaterFeature',
            'outFields': '*',
            'returnIntersection': 'true',
            'locationType': 'street'
        }
        return await self._make_request('reverseGeocode', params, 'geocoding')