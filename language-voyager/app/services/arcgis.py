from fastapi import HTTPException
from sqlalchemy.orm import Session
import aiohttp
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis
from ..core.config import get_settings
from ..models.arcgis_usage import ArcGISUsage

settings = get_settings()
redis_client = redis.from_url(settings.REDIS_URL)

class ArcGISCredit:
    # Credit costs per operation (based on ArcGIS documentation)
    CREDIT_COSTS = {
        'geocoding': 0.04,
        'routing': 0.005,
        'tile_request': 0.001,
        'feature_request': 0.002
    }

class ArcGISService:
    def __init__(self, db: Session):
        self.db = db
        self.api_key = settings.ARCGIS_API_KEY
        if not self.api_key:
            raise ValueError("ArcGIS API key is not configured")

    async def _check_credit_limit(self, operation_type: str) -> bool:
        """Check if operation would exceed daily credit limit"""
        current_usage = ArcGISUsage.get_daily_usage(self.db)
        operation_cost = ArcGISCredit.CREDIT_COSTS.get(operation_type, 0.04)  # Default to highest cost
        return current_usage + operation_cost <= settings.ARCGIS_MAX_CREDITS_PER_DAY

    def _log_credit_usage(self, operation_type: str):
        """Log credit usage to database"""
        usage = ArcGISUsage(
            operation_type=operation_type,
            credits_used=ArcGISCredit.CREDIT_COSTS.get(operation_type, 0.04)
        )
        self.db.add(usage)
        self.db.commit()

    async def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if available"""
        cached = redis_client.get(cache_key)
        return json.loads(cached) if cached else None

    async def _cache_response(self, cache_key: str, response: Dict):
        """Cache response with expiration"""
        redis_client.setex(
            cache_key,
            settings.ARCGIS_CACHE_DURATION,
            json.dumps(response)
        )

    async def _make_request(self, endpoint: str, params: Dict[str, Any], operation_type: str) -> Dict:
        """Make an ArcGIS API request with credit management"""
        # Check cache first
        cache_key = f"arcgis:{endpoint}:{json.dumps(params, sort_keys=True)}"
        cached_response = await self._get_cached_response(cache_key)
        if cached_response:
            return cached_response

        # Check credit limit
        if not await self._check_credit_limit(operation_type):
            raise HTTPException(
                status_code=429,
                detail="Daily ArcGIS credit limit reached. Please try again tomorrow."
            )

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
        self._log_credit_usage(operation_type)
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