"""
快取裝飾器

提供函式結果快取功能。
符合 T-5-4-2：效能優化
"""

from functools import wraps
from typing import Callable, Any, Optional
import hashlib
import json
from shared_kernel.infrastructure.cache import get_cache_service
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


def cache_result(
    ttl: int = 300,
    key_prefix: Optional[str] = None,
) -> Callable:
    """
    快取函式結果的裝飾器
    
    Args:
        ttl: 快取過期時間（秒）
        key_prefix: 快取鍵前綴
    
    Returns:
        Callable: 裝飾器函式
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 生成快取鍵
            cache_key = _generate_cache_key(func, key_prefix, args, kwargs)
            
            # 嘗試從快取取得結果
            cache_service = await get_cache_service()
            cached_result = await cache_service.get(cache_key)
            
            if cached_result is not None:
                logger.debug("從快取取得結果", extra={"key": cache_key, "function": func.__name__})
                return cached_result
            
            # 執行函式
            result = await func(*args, **kwargs)
            
            # 將結果存入快取
            await cache_service.set(cache_key, result, ttl=ttl)
            logger.debug("將結果存入快取", extra={"key": cache_key, "function": func.__name__})
            
            return result
        
        return wrapper
    return decorator


def _generate_cache_key(
    func: Callable,
    key_prefix: Optional[str],
    args: tuple,
    kwargs: dict,
) -> str:
    """
    生成快取鍵
    
    Args:
        func: 函式
        key_prefix: 鍵前綴
        args: 位置參數
        kwargs: 關鍵字參數
    
    Returns:
        str: 快取鍵
    """
    prefix = key_prefix or f"cache:{func.__module__}:{func.__name__}"
    
    # 將參數序列化為字串
    key_data = {
        "args": args,
        "kwargs": kwargs,
    }
    key_string = json.dumps(key_data, default=str, sort_keys=True)
    
    # 生成雜湊值
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"{prefix}:{key_hash}"

