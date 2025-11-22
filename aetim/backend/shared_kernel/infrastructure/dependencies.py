"""
共享核心依賴注入

提供跨模組使用的依賴注入函數。
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from shared_kernel.infrastructure.database import get_db
from system_management.application.services.audit_log_service import AuditLogService
from system_management.infrastructure.persistence.audit_log_repository import AuditLogRepository


def get_audit_log_service(
    db: AsyncSession = Depends(get_db),
) -> AuditLogService:
    """
    取得稽核日誌服務
    
    Args:
        db: 資料庫 Session
    
    Returns:
        AuditLogService: 稽核日誌服務
    """
    repository = AuditLogRepository(db)
    return AuditLogService(repository)

