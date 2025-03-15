from typing import Dict, List, Optional
import json
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.region import Region
from ..models.poi import PointOfInterest
from ..services.arcgis import ArcGISService
from ..services.cache import cache

class OfflineMapService:
    def __init__(self, db: Session):
        self.db = db
        self.arcgis_service = ArcGISService(db)

    async def prepare_offline_package(
        self,
        region_id: str,
        bounds: Dict,
        zoom_levels: List[int] = [12, 13, 14, 15, 16]
    ) -> Dict:
        """
        Prepare an offline package for a region including:
        - Map tiles for specified zoom levels
        - POI data
        - Region metadata
        """
        # Get region data
        region = self.db.query(Region).filter(Region.id == region_id).first()
        if not region:
            raise ValueError(f"Region {region_id} not found")

        # Get POIs for region
        pois = self.db.query(PointOfInterest).filter(
            PointOfInterest.region_id == region_id
        ).all()

        # Get map tiles package from ArcGIS
        tile_package = await self.arcgis_service.generate_tile_package(
            bounds=bounds,
            zoom_levels=zoom_levels
        )

        # Prepare offline package
        offline_package = {
            "region": {
                "id": region.id,
                "name": region.name,
                "local_name": region.local_name,
                "bounds": region.bounds,
                "center": region.center,
                "metadata": region.region_metadata
            },
            "pois": [poi.to_dict() for poi in pois],
            "tile_package": tile_package,
            "timestamp": datetime.utcnow().isoformat(),
            "zoom_levels": zoom_levels
        }

        # Cache the package
        cache_key = f"offline_package:{region_id}"
        await cache.set(cache_key, json.dumps(offline_package))

        return offline_package

    async def get_cached_package(self, region_id: str) -> Optional[Dict]:
        """Get a cached offline package for a region"""
        cache_key = f"offline_package:{region_id}"
        cached = await cache.get(cache_key)
        return json.loads(cached) if cached else None

    async def check_package_status(
        self,
        region_id: str,
        timestamp: Optional[str] = None
    ) -> Dict:
        """
        Check if an offline package needs updating
        Returns status and update info if needed
        """
        cached_package = await self.get_cached_package(region_id)
        if not cached_package:
            return {
                "status": "not_found",
                "needs_update": True
            }

        if not timestamp:
            return {
                "status": "ok",
                "needs_update": True,
                "current_timestamp": cached_package["timestamp"]
            }

        cached_time = datetime.fromisoformat(cached_package["timestamp"])
        check_time = datetime.fromisoformat(timestamp)

        return {
            "status": "ok",
            "needs_update": cached_time > check_time,
            "current_timestamp": cached_package["timestamp"]
        }

    async def sync_offline_changes(
        self,
        region_id: str,
        offline_data: Dict
    ) -> Dict:
        """
        Sync any changes made while offline
        - User progress
        - Completed challenges
        - etc.
        """
        # TODO: Implement conflict resolution for offline changes
        return {
            "status": "synced",
            "timestamp": datetime.utcnow().isoformat()
        }