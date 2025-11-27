"""
系統狀態 API 控制器

提供系統狀態監控的 API 端點。
符合 AC-027-2, AC-027-3。
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from system_management.application.services.health_check_service import HealthCheckService
from shared_kernel.infrastructure.database import get_db
from system_management.infrastructure.decorators.authorization import require_permission
from system_management.domain.value_objects.permission_name import PermissionName

router = APIRouter(prefix="/api/v1/system-status", tags=["系統狀態"])


def get_health_check_service(
    db_session: AsyncSession = Depends(get_db),
) -> HealthCheckService:
    """
    取得健康檢查服務
    
    Args:
        db_session: 資料庫 Session
    
    Returns:
        HealthCheckService: 健康檢查服務
    """
    return HealthCheckService(db_session)


@router.get("")
@require_permission(PermissionName.SYSTEM_CONFIG_VIEW)
async def get_system_status(
    service: HealthCheckService = Depends(get_health_check_service),
) -> Dict[str, Any]:
    """
    取得系統狀態
    
    符合 AC-027-2：儀表板必須顯示所有必要資訊
    
    Returns:
        Dict[str, Any]: 系統狀態資訊
    """
    return await service.get_system_status()


@router.get("/health")
async def health_check(
    service: HealthCheckService = Depends(get_health_check_service),
) -> Dict[str, Any]:
    """
    健康檢查端點
    
    符合 AC-027-3：提供健康檢查端點
    
    Returns:
        Dict[str, Any]: 健康檢查結果
    """
    return await service.check_health()

