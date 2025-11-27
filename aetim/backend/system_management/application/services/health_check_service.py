"""
健康檢查服務

提供系統健康檢查和狀態監控功能。
符合 AC-027-2, AC-027-3。
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from threat_intelligence.infrastructure.persistence.models import ThreatFeed, Threat
from analysis_assessment.infrastructure.persistence.models import RiskAssessment
from shared_kernel.infrastructure.database import engine
from shared_kernel.infrastructure.redis import check_redis_health
from shared_kernel.infrastructure.logging import get_logger
import httpx
import os

logger = get_logger(__name__)


class HealthCheckService:
    """
    健康檢查服務
    
    提供系統健康檢查和狀態監控功能。
    符合 AC-027-2：儀表板必須顯示所有必要資訊
    符合 AC-027-3：提供健康檢查端點
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        初始化健康檢查服務
        
        Args:
            db_session: 資料庫 Session
        """
        self.db_session = db_session
    
    async def check_health(self) -> Dict[str, Any]:
        """
        檢查系統健康狀態
        
        符合 AC-027-3：提供健康檢查端點
        
        Returns:
            Dict[str, Any]: 健康檢查結果
        """
        checks = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }
        
        # 檢查資料庫
        db_healthy, db_status = await self._check_database()
        checks["checks"]["database"] = db_status
        if not db_healthy:
            checks["status"] = "unhealthy"
        
        # 檢查 Redis
        redis_healthy, redis_status = await self._check_redis()
        checks["checks"]["redis"] = redis_status
        if not redis_healthy:
            checks["status"] = "unhealthy"
        
        # 檢查 AI 服務（非關鍵服務）
        ai_healthy, ai_status = await self._check_ai_service()
        checks["checks"]["ai_service"] = ai_status
        if not ai_healthy and checks["status"] == "healthy":
            checks["status"] = "degraded"
        
        return checks
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        取得系統狀態
        
        符合 AC-027-2：儀表板必須顯示所有必要資訊
        
        Returns:
            Dict[str, Any]: 系統狀態資訊
        """
        # 取得威脅情資收集狀態
        threat_collection_status = await self._get_threat_collection_status()
        
        # 取得最近收集的威脅數量
        recent_threat_count = await self._get_recent_threat_count()
        
        # 取得待處理的嚴重威脅數量
        critical_threat_count = await self._get_critical_threat_count()
        
        # 取得系統健康狀態
        health_status = await self.check_health()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "threat_collection_status": threat_collection_status,
            "recent_threat_count": recent_threat_count,
            "critical_threat_count": critical_threat_count,
            "system_health": health_status,
        }
    
    async def _check_database(self) -> tuple[bool, str]:
        """
        檢查資料庫連線
        
        Returns:
            tuple[bool, str]: (是否健康, 狀態訊息)
        """
        try:
            from sqlalchemy import text
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True, "healthy"
        except Exception as e:
            logger.error("Database health check failed", extra={"error": str(e)})
            return False, f"unhealthy: {str(e)}"
    
    async def _check_redis(self) -> tuple[bool, str]:
        """
        檢查 Redis 連線
        
        Returns:
            tuple[bool, str]: (是否健康, 狀態訊息)
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
    
    async def _check_ai_service(self) -> tuple[bool, str]:
        """
        檢查 AI 服務連線
        
        Returns:
            tuple[bool, str]: (是否健康, 狀態訊息)
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
    
    async def _get_threat_collection_status(self) -> List[Dict[str, Any]]:
        """
        取得威脅情資收集狀態
        
        符合 AC-027-2：威脅情資收集狀態（各來源的最後收集時間與狀態）
        
        Returns:
            List[Dict[str, Any]]: 威脅情資收集狀態清單
        """
        result = await self.db_session.execute(
            select(ThreatFeed)
            .where(ThreatFeed.is_enabled == True)
            .order_by(ThreatFeed.priority, ThreatFeed.name)
        )
        feeds = result.scalars().all()
        
        status_list = []
        for feed in feeds:
            # 判斷狀態
            status = "unknown"
            if feed.last_collection_status == "Success":
                # 檢查是否超過預期收集時間
                if feed.last_collection_time:
                    # 根據收集頻率判斷是否過期
                    expected_interval = self._get_expected_interval(feed.collection_frequency)
                    if expected_interval:
                        time_since_last = datetime.utcnow() - feed.last_collection_time
                        if time_since_last > timedelta(seconds=expected_interval * 2):
                            status = "warning"
                        else:
                            status = "healthy"
                    else:
                        status = "healthy"
                else:
                    status = "warning"
            elif feed.last_collection_status == "Failed":
                status = "error"
            
            status_list.append({
                "feed_id": feed.id,
                "feed_name": feed.name,
                "priority": feed.priority,
                "last_collection_time": feed.last_collection_time.isoformat() if feed.last_collection_time else None,
                "last_collection_status": feed.last_collection_status,
                "status": status,
                "collection_frequency": feed.collection_frequency,
            })
        
        return status_list
    
    async def _get_recent_threat_count(self) -> Dict[str, Any]:
        """
        取得最近收集的威脅數量
        
        符合 AC-027-2：最近收集的威脅數量
        
        Returns:
            Dict[str, Any]: 威脅數量統計
        """
        # 最近 24 小時
        last_24h = datetime.utcnow() - timedelta(hours=24)
        result_24h = await self.db_session.execute(
            select(func.count(Threat.id))
            .where(Threat.created_at >= last_24h)
        )
        count_24h = result_24h.scalar() or 0
        
        # 最近 7 天
        last_7d = datetime.utcnow() - timedelta(days=7)
        result_7d = await self.db_session.execute(
            select(func.count(Threat.id))
            .where(Threat.created_at >= last_7d)
        )
        count_7d = result_7d.scalar() or 0
        
        return {
            "last_24_hours": count_24h,
            "last_7_days": count_7d,
        }
    
    async def _get_critical_threat_count(self) -> int:
        """
        取得待處理的嚴重威脅數量
        
        符合 AC-027-2：待處理的嚴重威脅數量
        
        Returns:
            int: 嚴重威脅數量
        """
        result = await self.db_session.execute(
            select(func.count(RiskAssessment.id))
            .where(
                and_(
                    RiskAssessment.risk_score >= 8.0,
                    RiskAssessment.status == "Active",
                )
            )
        )
        return result.scalar() or 0
    
    def _get_expected_interval(self, frequency: str) -> int | None:
        """
        取得預期收集間隔（秒）
        
        Args:
            frequency: 收集頻率
        
        Returns:
            int | None: 預期間隔（秒），如果無法判斷則返回 None
        """
        frequency_lower = frequency.lower()
        if "每小時" in frequency_lower or "hourly" in frequency_lower:
            return 3600
        elif "每日" in frequency_lower or "daily" in frequency_lower:
            return 86400
        elif "每週" in frequency_lower or "weekly" in frequency_lower:
            return 604800
        return None

