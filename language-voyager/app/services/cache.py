from typing import Optional, Any
import json
from redis import Redis
from ..core.config import get_settings

class RedisCache:
    def __init__(self):
        settings = get_settings()
        self.redis = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        self.default_ttl = 3600  # 1 hour default TTL

    async def get_poi_content(self, poi_id: str, language: str, proficiency_level: float) -> Optional[dict]:
        """Get cached POI content"""
        key = f"poi_content:{poi_id}:{language}:{int(proficiency_level)}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    async def set_poi_content(self, poi_id: str, language: str, proficiency_level: float, content: dict, ttl: int = None):
        """Cache POI content with TTL"""
        key = f"poi_content:{poi_id}:{language}:{int(proficiency_level)}"
        self.redis.setex(
            key,
            ttl or self.default_ttl,
            json.dumps(content)
        )

    async def invalidate_poi_content(self, poi_id: str):
        """Invalidate all cached content for a POI"""
        pattern = f"poi_content:{poi_id}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)

# Global cache instance
cache = RedisCache()