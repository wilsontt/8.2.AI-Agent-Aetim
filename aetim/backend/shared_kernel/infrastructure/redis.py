"""
Redis 連線設定

實作 Redis 連線與操作，用於快取與事件匯流排。
"""

import redis.asyncio as aioredis
import os
from typing import Optional

# Redis 連線設定（從環境變數讀取）
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Redis 連線池
_redis_pool: Optional[aioredis.ConnectionPool] = None
_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """
    取得 Redis 客戶端（依賴注入用）
    
    Returns:
        aioredis.Redis: Redis 客戶端
    """
    global _redis_client
    
    if _redis_client is None:
        await init_redis()
    
    return _redis_client


async def init_redis() -> None:
    """
    初始化 Redis 連線
    
    建立 Redis 連線池與客戶端。
    """
    global _redis_pool, _redis_client
    
    if _redis_pool is None:
        _redis_pool = aioredis.ConnectionPool.from_url(
            REDIS_URL,
            max_connections=10,
            decode_responses=True,
        )
    
    if _redis_client is None:
        _redis_client = aioredis.Redis(connection_pool=_redis_pool)


async def close_redis() -> None:
    """
    關閉 Redis 連線
    
    關閉連線池與客戶端。
    """
    global _redis_pool, _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None


async def check_redis_health() -> bool:
    """
    檢查 Redis 連線健康狀態
    
    Returns:
        bool: Redis 連線是否正常
    """
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        return True
    except Exception:
        return False

