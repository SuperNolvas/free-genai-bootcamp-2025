from typing import Dict, List, Optional
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from ..models.poi import PointOfInterest
from ..models.progress import UserProgress
from ..models.achievement import Achievement
from ..core.config import get_settings

settings = get_settings()

SCHEMA = """
CREATE TABLE IF NOT EXISTS offline_packages (
    region_id TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    version TEXT NOT NULL,
    stored_at TEXT NOT NULL,
    expires_at TEXT
);

CREATE TABLE IF NOT EXISTS pending_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    synced INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pending_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    synced INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pending_downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT NOT NULL,
    type TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS content_versions (
    region_id TEXT NOT NULL,
    content_type TEXT NOT NULL,
    version TEXT NOT NULL,
    last_sync TEXT NOT NULL,
    PRIMARY KEY (region_id, content_type)
);
"""

class LocalStorageService:
    """Service for managing local storage and offline data synchronization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.local_db_path = Path(settings.LOCAL_STORAGE_PATH) / "offline.db"
        self._init_local_storage()
        
    def _init_local_storage(self):
        """Initialize local SQLite database"""
        self.local_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(str(self.local_db_path)) as conn:
            conn.executescript(SCHEMA)
            conn.commit()
        
    async def store_offline_package(self, region_id: str, package_data: Dict) -> Dict:
        """Store map package data for offline use"""
        try:
            # Store package metadata and data
            with sqlite3.connect(str(self.local_db_path)) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO offline_packages 
                    (region_id, data, version, stored_at, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        region_id,
                        json.dumps(package_data),
                        package_data.get("version", "1.0"),
                        datetime.utcnow().isoformat(),
                        package_data.get("expires_at")
                    )
                )
                conn.commit()
            
            # Return storage confirmation
            return {
                "status": "stored",
                "metadata": {
                    "region_id": region_id,
                    "stored_at": datetime.utcnow().isoformat(),
                    "version": package_data.get("version"),
                    "expires_at": package_data.get("expires_at"),
                    "tile_count": len(package_data.get("tiles", [])),
                    "poi_count": len(package_data.get("pois", [])),
                },
                "storage_location": str(self.local_db_path)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_pending_changes(self, region_id: str, user_id: int) -> Dict:
        """Get pending changes that need to be synced"""
        try:
            with sqlite3.connect(str(self.local_db_path)) as conn:
                # Get offline progress updates
                progress_updates = self._get_pending_progress(conn, region_id, user_id)
                
                # Get offline achievements
                achievement_updates = self._get_pending_achievements(conn, region_id, user_id)
                
                # Get pending downloads
                pending_downloads = self._get_pending_downloads(conn, region_id)
                
                # Get content version info
                content_versions = self._get_content_versions(conn, region_id)
                
                return {
                    "progress_updates": progress_updates,
                    "achievement_updates": achievement_updates,
                    "pending_downloads": pending_downloads,
                    "content_versions": content_versions,
                    "last_sync_timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _get_pending_progress(self, conn: sqlite3.Connection, region_id: str, user_id: int) -> List[Dict]:
        """Get pending progress updates from local storage"""
        cursor = conn.execute(
            """
            SELECT data FROM pending_progress 
            WHERE region_id = ? AND user_id = ? AND synced = 0
            ORDER BY created_at ASC
            """,
            (region_id, user_id)
        )
        return [json.loads(row[0]) for row in cursor.fetchall()]

    def _get_pending_achievements(self, conn: sqlite3.Connection, region_id: str, user_id: int) -> List[Dict]:
        """Get pending achievement updates from local storage"""
        cursor = conn.execute(
            """
            SELECT data FROM pending_achievements
            WHERE region_id = ? AND user_id = ? AND synced = 0
            ORDER BY created_at ASC
            """,
            (region_id, user_id)
        )
        return [json.loads(row[0]) for row in cursor.fetchall()]

    def _get_pending_downloads(self, conn: sqlite3.Connection, region_id: str) -> List[Dict]:
        """Get list of pending tile/POI downloads"""
        cursor = conn.execute(
            """
            SELECT type, data FROM pending_downloads
            WHERE region_id = ? AND completed = 0
            ORDER BY created_at ASC
            """,
            (region_id,)
        )
        return [{"type": row[0], **json.loads(row[1])} for row in cursor.fetchall()]

    def _get_content_versions(self, conn: sqlite3.Connection, region_id: str) -> Dict:
        """Get stored content version information"""
        cursor = conn.execute(
            """
            SELECT content_type, version, last_sync 
            FROM content_versions
            WHERE region_id = ?
            """,
            (region_id,)
        )
        return {
            row[0]: {
                "version": row[1],
                "last_sync": row[2]
            } for row in cursor.fetchall()
        }

    async def process_sync_response(self, region_id: str, sync_response: Dict) -> Dict:
        """Process server sync response and update local storage"""
        try:
            if sync_response.get("status") == "synced":
                with sqlite3.connect(str(self.local_db_path)) as conn:
                    # Update local content if there are updates
                    if sync_response.get("content_updates"):
                        await self._update_local_content(
                            conn,
                            region_id,
                            sync_response["content_updates"]
                        )
                    
                    # Clear synced changes
                    self._clear_synced_changes(conn, region_id)
                    
                    # Update sync timestamp
                    self._update_sync_timestamp(conn, region_id)
                    
                    conn.commit()
                
                return {
                    "status": "processed",
                    "changes_applied": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return {
                "status": "error",
                "error": "Invalid sync response"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _update_local_content(self, conn: sqlite3.Connection, region_id: str, content_updates: Dict):
        """Update locally stored content with server changes"""
        for content_type, update in content_updates.items():
            conn.execute(
                """
                INSERT OR REPLACE INTO content_versions
                (region_id, content_type, version, last_sync)
                VALUES (?, ?, ?, ?)
                """,
                (
                    region_id,
                    content_type,
                    update["version"],
                    datetime.utcnow().isoformat()
                )
            )
    
    def _clear_synced_changes(self, conn: sqlite3.Connection, region_id: str):
        """Clear changes that have been successfully synced"""
        conn.execute(
            "UPDATE pending_progress SET synced = 1 WHERE region_id = ?",
            (region_id,)
        )
        conn.execute(
            "UPDATE pending_achievements SET synced = 1 WHERE region_id = ?",
            (region_id,)
        )
    
    def _update_sync_timestamp(self, conn: sqlite3.Connection, region_id: str):
        """Update last sync timestamp for all content types"""
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            UPDATE content_versions 
            SET last_sync = ? 
            WHERE region_id = ?
            """,
            (now, region_id)
        )