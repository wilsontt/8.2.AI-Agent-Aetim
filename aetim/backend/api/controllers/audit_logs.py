"""
稽核日誌控制器

提供稽核日誌查詢的 API 端點。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from shared_kernel.infrastructure.database import get_db
from shared_kernel.infrastructure.logging import get_logger
from system_management.application.services.audit_log_service import AuditLogService
from system_management.application.dtos.audit_log_dto import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogFilterRequest,
)
from system_management.infrastructure.persistence.audit_log_repository import AuditLogRepository

logger = get_logger(__name__)
router = APIRouter()


def get_audit_log_service(db: AsyncSession = Depends(get_db)) -> AuditLogService:
    """
    取得稽核日誌服務
    
    Args:
        db: 資料庫 Session
    
    Returns:
        AuditLogService: 稽核日誌服務
    """
    repository = AuditLogRepository(db)
    return AuditLogService(repository)


@router.get("", response_model=AuditLogListResponse, summary="查詢稽核日誌清單")
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="使用者 ID"),
    action: Optional[str] = Query(None, description="操作類型（CREATE/UPDATE/DELETE/IMPORT/VIEW/TOGGLE/EXPORT）"),
    resource_type: Optional[str] = Query(None, description="資源類型（Asset/PIR/ThreatFeed 等）"),
    resource_id: Optional[str] = Query(None, description="資源 ID"),
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    page: int = Query(1, ge=1, description="頁碼（從 1 開始）"),
    page_size: int = Query(20, ge=1, le=100, description="每頁筆數"),
    sort_by: Optional[str] = Query(None, description="排序欄位（created_at/action/resource_type）"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向（asc/desc）"),
    service: AuditLogService = Depends(get_audit_log_service),
):
    """
    查詢稽核日誌清單
    
    支援多種篩選條件和分頁。
    """
    try:
        request = AuditLogFilterRequest(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        response = await service.get_audit_logs(request)
        return response
    except ValueError as e:
        logger.warning("查詢稽核日誌失敗：無效的參數", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("查詢稽核日誌失敗", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢稽核日誌時發生錯誤",
        )


@router.get("/{audit_log_id}", response_model=AuditLogResponse, summary="取得稽核日誌詳情")
async def get_audit_log_by_id(
    audit_log_id: str,
    service: AuditLogService = Depends(get_audit_log_service),
):
    """
    取得稽核日誌詳情
    
    Args:
        audit_log_id: 稽核日誌 ID
        service: 稽核日誌服務
    """
    try:
        audit_log = await service.get_audit_log_by_id(audit_log_id)
        
        if not audit_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到稽核日誌：{audit_log_id}",
            )
        
        return audit_log
    except HTTPException:
        raise
    except Exception as e:
        logger.error("取得稽核日誌詳情失敗", extra={"error": str(e), "audit_log_id": audit_log_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得稽核日誌詳情時發生錯誤",
        )

