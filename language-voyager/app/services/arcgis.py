from fastapi import HTTPException
from sqlalchemy.orm import Session
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import redis
import hashlib
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
        self.api_key = settings.ARCGIS_API_KEY
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
        """Check both daily credit and monthly operation limits"""
        # Check daily credit limit
        current_usage = ArcGISUsage.get_daily_usage(self.db)
        operation_cost = ArcGISCredit.CREDIT_COSTS.get(operation_type, 0.04)
        if current_usage + operation_cost > settings.ARCGIS_MAX_CREDITS_PER_DAY:
            raise HTTPException(
                status_code=429,
                detail="Daily ArcGIS credit limit reached. Please try again tomorrow."
            )

        # Check monthly operation limit and get alert level
        within_limit, usage_percentage, alert_level = ArcGISUsage.check_monthly_limit(
            self.db, operation_type
        )

        if not within_limit:
            raise HTTPException(
                status_code=429,
                detail=f"Monthly limit for {operation_type} operations reached. Please try again next month."
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
        params['token'] = self.api_key
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://www.arcgis.com/sharing/rest/{endpoint}", params=params) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="ArcGIS API request failed"
                    )
                result = await response.json()

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
            'outFields': '*'
        }
        return await self._make_request('geocode', params, 'geocoding')

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