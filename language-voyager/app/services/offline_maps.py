from typing import Dict, List, Optional
import json
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.region import Region
from ..models.poi import PointOfInterest
from ..models.progress import UserProgress
from ..services.arcgis import ArcGISService
from ..services.cache import cache
from ..core.config import get_settings

settings = get_settings()

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
        - User progress data
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

        # Get user progress data for offline sync
        progress_records = self.db.query(UserProgress).filter(
            UserProgress.region_id == region_id
        ).all()

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
            "progress": [p.to_dict() for p in progress_records],
            "timestamp": datetime.utcnow().isoformat(),
            "zoom_levels": zoom_levels,
            "version": "2.0"
        }

        # Cache the package
        cache_key = f"offline_package:{region_id}"
        await cache.set(
            cache_key,
            json.dumps(offline_package),
            expire=settings.OFFLINE_PACKAGE_TTL
        )

        return offline_package

    async def get_cached_package(self, region_id: str) -> Optional[Dict]:
        """Get a cached offline package for a region"""
        cache_key = f"offline_package:{region_id}"
        cached = await cache.get(cache_key)
        return json.loads(cached) if cached else None

    async def check_package_status(
        self,
        region_id: str,
        timestamp: Optional[str] = None,
        version: Optional[str] = None
    ) -> Dict:
        """
        Check if an offline package needs updating
        Args:
            region_id: The region ID to check
            timestamp: Client's current package timestamp
            version: Client's current package version
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
                "current_timestamp": cached_package["timestamp"],
                "current_version": cached_package.get("version", "1.0")
            }

        cached_time = datetime.fromisoformat(cached_package["timestamp"])
        check_time = datetime.fromisoformat(timestamp)

        # Check version compatibility
        current_version = cached_package.get("version", "1.0")
        needs_version_update = version != current_version if version else True

        return {
            "status": "ok",
            "needs_update": cached_time > check_time or needs_version_update,
            "current_timestamp": cached_package["timestamp"],
            "current_version": current_version
        }

    async def sync_offline_changes(
        self,
        region_id: str,
        offline_data: Dict
    ) -> Dict:
        """
        Sync changes made while offline
        Args:
            region_id: The region ID to sync
            offline_data: Dict containing:
                - progress_updates: List of progress records
                - last_sync_timestamp: Last sync timestamp
                - pending_downloads: List of pending tile downloads
        """
        try:
            # Get the current server state
            server_package = await self.get_cached_package(region_id)
            if not server_package:
                raise ValueError("Server package not found")

            # Process progress updates
            progress_updates = offline_data.get("progress_updates", [])
            for progress in progress_updates:
                await self._merge_progress_update(progress)

            # Handle pending downloads
            pending_downloads = offline_data.get("pending_downloads", [])
            if pending_downloads:
                await self._process_pending_downloads(region_id, pending_downloads)

            # Get updated server state after processing changes
            updated_package = await self.get_cached_package(region_id)

            return {
                "status": "synced",
                "timestamp": datetime.utcnow().isoformat(),
                "changes_processed": len(progress_updates),
                "downloads_processed": len(pending_downloads),
                "current_package": updated_package
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _merge_progress_update(self, progress_data: Dict):
        """Merge a progress update from offline data"""
        progress = UserProgress(
            user_id=progress_data["user_id"],
            region_id=progress_data["region_id"],
            type=progress_data["type"],
            value=progress_data["value"],
            timestamp=datetime.fromisoformat(progress_data["timestamp"])
        )
        self.db.merge(progress)
        self.db.commit()

    async def _process_pending_downloads(self, region_id: str, pending_downloads: List[Dict]):
        """Process any pending tile or POI downloads"""
        # Get current package
        package = await self.get_cached_package(region_id)
        if not package:
            return

        # Add missing tiles
        for download in pending_downloads:
            if download["type"] == "tile":
                zoom = download["zoom"]
                x = download["x"]
                y = download["y"]
                if str(zoom) not in package["tile_package"]["tiles"]:
                    package["tile_package"]["tiles"][str(zoom)] = []
                
                # Check if tile already exists
                tile_exists = any(
                    t["x"] == x and t["y"] == y 
                    for t in package["tile_package"]["tiles"][str(zoom)]
                )
                
                if not tile_exists:
                    url = f"https://basemaps.arcgis.com/arcgis/rest/services/World_Basemap/tile/{zoom}/{y}/{x}"
                    package["tile_package"]["tiles"][str(zoom)].append({
                        "url": url,
                        "x": x,
                        "y": y,
                        "z": zoom
                    })

        # Update cache with new package
        cache_key = f"offline_package:{region_id}"
        await cache.set(
            cache_key,
            json.dumps(package),
            expire=settings.OFFLINE_PACKAGE_TTL
        )