"""
健康檢查控制器

提供系統健康檢查端點，用於監控系統狀態。
符合 plan.md 第 9.3.2 節的要求。
"""

from fastapi import APIRouter, status, HTTPException
from datetime import datetime
from typing import Dict, Any
from shared_kernel.infrastructure.database import engine
from shared_kernel.infrastructure.redis import check_redis_health
from shared_kernel.infrastructure.logging import get_logger
import httpx
import os

router = APIRouter()
logger = get_logger(__name__)


async def check_database() -> tuple[bool, str]:
    """
    檢查資料庫連線
    
    Returns:
        (是否健康, 狀態訊息)
    """
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "healthy"
    except Exception as e:
        logger.error("Database health check failed", extra={"error": str(e)})
        return False, f"unhealthy: {str(e)}"


async def check_redis() -> tuple[bool, str]:
    """
    檢查 Redis 連線
    
    Returns:
        (是否健康, 狀態訊息)
    """
    try:
        is_healthy = await check_redis_health()
        if is_healthy:
            return True, "healthy"
        else:
            return False, "unhealthy: connection failed"
    except Exception as e:
        logger.error("Redis health check failed", extra={"error": str(e)})
        return False, f"unhealthy: {str(e)}"


async def check_ai_service() -> tuple[bool, str]:
    """
    檢查 AI 服務連線
    
    Returns:
        (是否健康, 狀態訊息)
    """
    ai_service_url = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ai_service_url}/health")
            if response.status_code == 200:
                return True, "healthy"
            else:
                return False, f"unhealthy: status {response.status_code}"
    except Exception as e:
        logger.warn("AI service health check failed", extra={"error": str(e)})
        return False, f"unhealthy: {str(e)}"


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    健康檢查端點
    
    回應系統基本健康狀態，包含：
    - status: 系統狀態（healthy/unhealthy/degraded）
    - timestamp: 檢查時間
    - checks: 各項檢查結果（資料庫、Redis、AI 服務）
    
    狀態說明：
    - healthy: 所有檢查都通過
    - degraded: 非關鍵服務（如 AI 服務）失敗，但主要功能正常
    - unhealthy: 關鍵服務（資料庫、Redis）失敗
    """
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    # 檢查資料庫
    db_healthy, db_status = await check_database()
    checks["checks"]["database"] = db_status
    if not db_healthy:
        checks["status"] = "unhealthy"

    # 檢查 Redis
    redis_healthy, redis_status = await check_redis()
    checks["checks"]["redis"] = redis_status
    if not redis_healthy:
        checks["status"] = "unhealthy"

    # 檢查 AI 服務（非關鍵服務）
    ai_healthy, ai_status = await check_ai_service()
    checks["checks"]["ai_service"] = ai_status
    if not ai_healthy and checks["status"] == "healthy":
        checks["status"] = "degraded"

    # 根據狀態決定 HTTP 狀態碼
    if checks["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=checks
        )

    return checks

