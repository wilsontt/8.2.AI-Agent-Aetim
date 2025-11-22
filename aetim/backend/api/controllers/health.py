"""
健康檢查控制器

提供系統健康檢查端點，用於監控系統狀態。
"""

from fastapi import APIRouter, status
from datetime import datetime
from typing import Dict, Any
from shared_kernel.infrastructure.database import engine
from shared_kernel.infrastructure.redis import check_redis_health

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    健康檢查端點
    
    回應系統基本健康狀態，包含：
    - status: 系統狀態（healthy/unhealthy）
    - timestamp: 檢查時間
    - checks: 各項檢查結果（資料庫、Redis）
    """
    # 檢查資料庫連線
    db_healthy = False
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            db_healthy = True
    except Exception:
        db_healthy = False
    
    # 檢查 Redis 連線
    redis_healthy = await check_redis_health()
    
    # 整體狀態
    overall_status = "healthy" if (db_healthy and redis_healthy) else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
        },
    }

