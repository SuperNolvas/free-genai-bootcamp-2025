import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from .offline_maps import OfflineMapService
from .local_storage import LocalStorageService
from ..core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class SyncManager:
    """Manages background synchronization of offline data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.offline_service = OfflineMapService(db)
        self.storage = LocalStorageService(db)
        self._sync_tasks = {}
        self._last_sync = {}
        self._is_running = False
    
    async def start(self):
        """Start the sync manager"""
        if self._is_running:
            return
            
        self._is_running = True
        asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the sync manager"""
        self._is_running = False
        
        # Cancel all running sync tasks
        for task in self._sync_tasks.values():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    async def schedule_sync(self, region_id: str, user_id: int, force: bool = False):
        """Schedule a sync for a region"""
        # Check if sync is already scheduled
        task_key = f"{region_id}:{user_id}"
        if task_key in self._sync_tasks and not self._sync_tasks[task_key].done():
            if not force:
                return
            
            # Cancel existing sync if forced
            self._sync_tasks[task_key].cancel()
            try:
                await self._sync_tasks[task_key]
            except asyncio.CancelledError:
                pass
        
        # Check minimum sync interval
        last_sync = self._last_sync.get(task_key)
        if last_sync and not force:
            elapsed = (datetime.utcnow() - last_sync).total_seconds()
            if elapsed < settings.MIN_SYNC_INTERVAL:
                return
        
        # Schedule new sync
        self._sync_tasks[task_key] = asyncio.create_task(
            self._sync_region(region_id, user_id)
        )
    
    async def _sync_region(self, region_id: str, user_id: int):
        """Perform sync for a region"""
        retries = 0
        while retries < settings.SYNC_RETRY_ATTEMPTS:
            try:
                # Get pending changes
                changes = await self.storage.get_pending_changes(region_id, user_id)
                
                if not changes.get("status") == "error":
                    # Perform sync
                    sync_result = await self.offline_service.sync_offline_changes(
                        region_id,
                        changes
                    )
                    
                    if sync_result.get("status") == "synced":
                        # Process sync response
                        await self.storage.process_sync_response(
                            region_id,
                            sync_result
                        )
                        
                        # Update last sync time
                        self._last_sync[f"{region_id}:{user_id}"] = datetime.utcnow()
                        return
                
                # If we get here, sync failed
                retries += 1
                if retries < settings.SYNC_RETRY_ATTEMPTS:
                    await asyncio.sleep(settings.SYNC_RETRY_DELAY)
                
            except Exception as e:
                logger.error(f"Sync error for region {region_id}: {e}")
                retries += 1
                if retries < settings.SYNC_RETRY_ATTEMPTS:
                    await asyncio.sleep(settings.SYNC_RETRY_DELAY)
    
    async def _cleanup_loop(self):
        """Periodically clean up completed sync tasks"""
        while self._is_running:
            try:
                # Remove completed tasks
                for task_key, task in list(self._sync_tasks.items()):
                    if task.done():
                        self._sync_tasks.pop(task_key)
                        
                        # Clean up old last sync times
                        if task_key in self._last_sync:
                            elapsed = datetime.utcnow() - self._last_sync[task_key]
                            if elapsed > timedelta(days=1):
                                self._last_sync.pop(task_key)
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
            
            await asyncio.sleep(60)  # Run cleanup every minute