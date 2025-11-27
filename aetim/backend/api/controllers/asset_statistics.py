"""
資產統計 API 控制器

提供資產統計的 API 端點。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from asset_management.application.services.asset_statistics_service import AssetStatisticsService
from asset_management.application.dtos.asset_statistics_dto import AssetStatisticsResponse
from shared_kernel.infrastructure.database import get_db
from system_management.infrastructure.decorators.authorization import require_permission
from system_management.domain.value_objects.permission_name import PermissionName
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/statistics/assets", tags=["資產統計"])


def get_asset_statistics_service(
    db_session: AsyncSession = Depends(get_db),
) -> AssetStatisticsService:
    """
    取得資產統計服務
    
    Args:
        db_session: 資料庫 Session
    
    Returns:
        AssetStatisticsService: 資產統計服務
    """
    return AssetStatisticsService(db_session)


@router.get("", response_model=AssetStatisticsResponse, summary="取得資產統計")
@require_permission(PermissionName.ASSET_VIEW)
async def get_asset_statistics(
    service: AssetStatisticsService = Depends(get_asset_statistics_service),
) -> AssetStatisticsResponse:
    """
    取得資產統計
    
    包含：
    - 資產總數統計
    - 依資產類型統計
    - 依資料敏感度統計
    - 依業務關鍵性統計
    - 受威脅影響的資產統計
    """
    try:
        result = await service.get_asset_statistics()
        
        return AssetStatisticsResponse(
            total_count=result["total_count"],
            by_type=result["by_type"],
            by_sensitivity=result["by_sensitivity"],
            by_criticality=result["by_criticality"],
            affected_assets=result["affected_assets"],
            public_facing_count=result["public_facing_count"],
        )
    except Exception as e:
        logger.error("取得資產統計失敗", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得資產統計時發生錯誤",
        )

