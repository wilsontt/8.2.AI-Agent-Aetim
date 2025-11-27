"""
快取服務

提供 Redis 快取功能，用於提升 API 回應時間。
符合 T-5-4-2：效能優化
"""

from typing import Optional, Any
import json
import redis.asyncio as redis
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    快取服務
    
    提供 Redis 快取功能。
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        初始化快取服務
        
        Args:
            redis_client: Redis 客戶端（可選）
        """
        self.redis_client = redis_client
        self._default_ttl = 300  # 預設 TTL 5 分鐘
    
    async def get(self, key: str) -> Optional[Any]:
        """
        取得快取值
        
        Args:
            key: 快取鍵
        
        Returns:
            Optional[Any]: 快取值，如果不存在則返回 None
        """
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning("取得快取值失敗", extra={"key": key, "error": str(e)})
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        設定快取值
        
        Args:
            key: 快取鍵
            value: 快取值
            ttl: 過期時間（秒），如果為 None 則使用預設值
        
        Returns:
            bool: 是否成功設定
        """
        if not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            ttl = ttl or self._default_ttl
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.warning("設定快取值失敗", extra={"key": key, "error": str(e)})
            return False
    
    async def delete(self, key: str) -> bool:
        """
        刪除快取值
        
        Args:
            key: 快取鍵
        
        Returns:
            bool: 是否成功刪除
        """
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning("刪除快取值失敗", extra={"key": key, "error": str(e)})
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        清除符合模式的所有快取鍵
        
        Args:
            pattern: 鍵模式（例如："cache:statistics:*"）
        
        Returns:
            int: 清除的鍵數量
        """
        if not self.redis_client:
            return 0
        
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self.redis_client.delete(*keys)
            
            return len(keys)
        except Exception as e:
            logger.warning("清除快取模式失敗", extra={"pattern": pattern, "error": str(e)})
            return 0


# 全域快取服務實例
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """
    取得快取服務實例
    
    Returns:
        CacheService: 快取服務實例
    """
    global _cache_service
    if _cache_service is None:
        from shared_kernel.infrastructure.redis import get_redis
        redis_client = await get_redis()
        _cache_service = CacheService(redis_client)
    return _cache_service

