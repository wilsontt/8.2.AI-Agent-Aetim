"""
威脅統計 API 控制器

提供威脅統計的 API 端點。
符合 AC-028-1, AC-028-2。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from threat_intelligence.application.services.threat_statistics_service import ThreatStatisticsService
from threat_intelligence.application.dtos.threat_statistics_dto import (
    ThreatTrendResponse,
    ThreatTrendDataPoint,
    RiskDistributionResponse,
    AffectedAssetStatisticsResponse,
    ThreatSourceStatisticsResponse,
    ThreatSourceStatisticsDataPoint,
)
from shared_kernel.infrastructure.database import get_db
from system_management.infrastructure.decorators.authorization import require_permission
from system_management.domain.value_objects.permission_name import PermissionName
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/statistics/threats", tags=["威脅統計"])


def get_threat_statistics_service(
    db_session: AsyncSession = Depends(get_db),
) -> ThreatStatisticsService:
    """
    取得威脅統計服務
    
    Args:
        db_session: 資料庫 Session
    
    Returns:
        ThreatStatisticsService: 威脅統計服務
    """
    return ThreatStatisticsService(db_session)


@router.get("/trend", response_model=ThreatTrendResponse, summary="取得威脅數量趨勢")
@require_permission(PermissionName.THREAT_VIEW)
async def get_threat_trend(
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    interval: str = Query("day", regex="^(day|week|month)$", description="時間間隔（day/week/month）"),
    service: ThreatStatisticsService = Depends(get_threat_statistics_service),
) -> ThreatTrendResponse:
    """
    取得威脅數量趨勢
    
    符合 AC-028-1：威脅數量趨勢（依時間）
    符合 AC-028-2：支援時間範圍篩選
    """
    try:
        data = await service.get_threat_trend(
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )
        
        # 設定預設時間範圍（如果未提供）
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            from datetime import timedelta
            if interval == "day":
                start_date = end_date - timedelta(days=30)
            elif interval == "week":
                start_date = end_date - timedelta(weeks=12)
            elif interval == "month":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
        
        return ThreatTrendResponse(
            data=[ThreatTrendDataPoint(date=item["date"], count=item["count"]) for item in data],
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            interval=interval,
        )
    except Exception as e:
        logger.error("取得威脅數量趨勢失敗", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得威脅數量趨勢時發生錯誤",
        )


@router.get("/risk-distribution", response_model=RiskDistributionResponse, summary="取得風險分數分布")
@require_permission(PermissionName.THREAT_VIEW)
async def get_risk_distribution(
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    service: ThreatStatisticsService = Depends(get_threat_statistics_service),
) -> RiskDistributionResponse:
    """
    取得風險分數分布
    
    符合 AC-028-1：風險分數分布（嚴重/高/中/低）
    """
    try:
        result = await service.get_risk_distribution(
            start_date=start_date,
            end_date=end_date,
        )
        
        return RiskDistributionResponse(
            distribution=result["distribution"],
            total=result["total"],
        )
    except Exception as e:
        logger.error("取得風險分數分布失敗", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得風險分數分布時發生錯誤",
        )


@router.get("/affected-assets", response_model=AffectedAssetStatisticsResponse, summary="取得受影響資產統計")
@require_permission(PermissionName.THREAT_VIEW)
async def get_affected_asset_statistics(
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    service: ThreatStatisticsService = Depends(get_threat_statistics_service),
) -> AffectedAssetStatisticsResponse:
    """
    取得受影響資產統計
    
    符合 AC-028-1：受影響資產統計（依資產類型、依資產重要性）
    """
    try:
        result = await service.get_affected_asset_statistics(
            start_date=start_date,
            end_date=end_date,
        )
        
        return AffectedAssetStatisticsResponse(
            by_type=result["by_type"],
            by_importance=result["by_importance"],
        )
    except Exception as e:
        logger.error("取得受影響資產統計失敗", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得受影響資產統計時發生錯誤",
        )


@router.get("/sources", response_model=ThreatSourceStatisticsResponse, summary="取得威脅來源統計")
@require_permission(PermissionName.THREAT_VIEW)
async def get_threat_source_statistics(
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    service: ThreatStatisticsService = Depends(get_threat_statistics_service),
) -> ThreatSourceStatisticsResponse:
    """
    取得威脅來源統計
    
    符合 AC-028-1：威脅來源統計（各來源的威脅數量）
    """
    try:
        data = await service.get_threat_source_statistics(
            start_date=start_date,
            end_date=end_date,
        )
        
        return ThreatSourceStatisticsResponse(
            data=[
                ThreatSourceStatisticsDataPoint(
                    source_name=item["source_name"],
                    priority=item["priority"],
                    count=item["count"],
                )
                for item in data
            ]
        )
    except Exception as e:
        logger.error("取得威脅來源統計失敗", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得威脅來源統計時發生錯誤",
        )

