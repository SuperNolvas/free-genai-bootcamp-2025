from typing import Optional, Any
import json
from redis.asyncio import Redis
from datetime import datetime, timedelta
from ..core.config import get_settings

class RedisCache:
    def __init__(self):
        settings = get_settings()
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.default_ttl = 3600  # 1 hour default TTL

    async def get(self, key: str, include_version: bool = False) -> Optional[Any]:
        """Get a value from cache, optionally with version info"""
        try:
            data = await self.redis.get(key)
            if not data:
                return None
                
            result = json.loads(data)
            if include_version:
                version_key = f"{key}:version"
                version = await self.redis.get(version_key)
                if version:
                    result["_version"] = int(version)
            return result
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None, version: int = None) -> bool:
        """Set a value in cache with optional versioning"""
        try:
            if ttl is None:
                ttl = self.default_ttl
                
            # Store the value
            await self.redis.set(
                key,
                json.dumps(value),
                ex=ttl
            )
            
            # Store version if provided
            if version is not None:
                version_key = f"{key}:version"
                await self.redis.set(version_key, str(version), ex=ttl)
                
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def invalidate(self, key: str) -> bool:
        """Remove a key from cache"""
        try:
            # Remove both value and version
            await self.redis.delete(key)
            await self.redis.delete(f"{key}:version")
            return True
        except Exception as e:
            print(f"Cache invalidate error: {e}")
            return False
    
    async def invalidate_poi_content(self, poi_id: str) -> bool:
        """Invalidate all cached content for a POI"""
        try:
            # Pattern to match all POI-related keys
            pattern = f"poi:{poi_id}:*"
            keys = []
            
            # Scan for matching keys
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            # Delete all matching keys
            if keys:
                await self.redis.delete(*keys)
            
            return True
        except Exception as e:
            print(f"POI content invalidation error: {e}")
            return False
    
    async def get_poi_content(
        self,
        poi_id: str,
        language: str,
        proficiency_level: float,
        client_version: Optional[int] = None
    ) -> Optional[dict]:
        """Get cached POI content with version validation"""
        key = f"poi:{poi_id}:content:{language}:{proficiency_level}"
        data = await self.get(key, include_version=True)
        
        if not data:
            return None
            
        # Version validation
        if client_version is not None:
            cache_version = data.get("_version")
            if not cache_version or cache_version != client_version:
                await self.invalidate(key)
                return None
                
        return data
    
    async def set_poi_content(
        self,
        poi_id: str,
        language: str,
        proficiency_level: float,
        content: dict,
        version: int
    ) -> bool:
        """Cache POI content with version information"""
        key = f"poi:{poi_id}:content:{language}:{proficiency_level}"
        return await self.set(key, content, version=version)

# Global cache instance
cache = RedisCache()