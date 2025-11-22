"""
稽核日誌服務

提供稽核日誌的記錄和查詢功能。
符合 ISO 27001:2022 要求（NFR-005）。
"""

from typing import Optional, Dict, Any
from datetime import datetime
from ...domain.interfaces.audit_log_repository import IAuditLogRepository
from ...domain.entities.audit_log import AuditLog
from ..dtos.audit_log_dto import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogFilterRequest,
)
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AuditLogService:
    """
    稽核日誌服務
    
    提供稽核日誌的記錄和查詢功能。
    符合 ISO 27001:2022 要求（NFR-005）。
    """
    
    def __init__(self, repository: IAuditLogRepository):
        """
        初始化服務
        
        Args:
            repository: 稽核日誌 Repository
        """
        self.repository = repository
    
    async def log_action(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """
        記錄操作
        
        符合 NFR-005 要求：
        - 記錄所有涉及資料存取、修改、刪除的操作
        - 包含：操作者、時間戳記、操作類型、資源識別碼、操作結果
        - 稽核日誌不可篡改（寫入後不可修改）
        
        Args:
            user_id: 使用者 ID（可選）
            action: 操作類型（CREATE/UPDATE/DELETE/IMPORT/VIEW/TOGGLE/EXPORT）
            resource_type: 資源類型（Asset/PIR/ThreatFeed 等）
            resource_id: 資源 ID（可選）
            details: 操作詳情（可選，字典格式，包含變更前後的值）
            ip_address: IP 位址（可選）
            user_agent: User Agent（可選）
        
        Returns:
            str: 稽核日誌 ID
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        try:
            # 建立稽核日誌實體
            audit_log = AuditLog.create(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            # 儲存稽核日誌
            await self.repository.save(audit_log)
            
            logger.info(
                "稽核日誌已記錄",
                extra={
                    "audit_log_id": audit_log.id,
                    "user_id": user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                }
            )
            
            return audit_log.id
        except Exception as e:
            logger.error(
                "記錄稽核日誌失敗",
                extra={
                    "user_id": user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise
    
    async def get_audit_logs(
        self,
        request: AuditLogFilterRequest,
    ) -> AuditLogListResponse:
        """
        查詢稽核日誌（支援多種篩選條件和分頁）
        
        Args:
            request: 稽核日誌篩選請求
        
        Returns:
            AuditLogListResponse: 稽核日誌清單回應
        """
        audit_logs, total_count = await self.repository.get_by_filters(
            user_id=request.user_id,
            action=request.action,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            start_date=request.start_date,
            end_date=request.end_date,
            page=request.page,
            page_size=request.page_size,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
        )
        
        # 計算總頁數
        total_pages = (total_count + request.page_size - 1) // request.page_size if total_count > 0 else 0
        
        # 轉換為回應格式
        audit_log_responses = [self._to_response(audit_log) for audit_log in audit_logs]
        
        return AuditLogListResponse(
            data=audit_log_responses,
            total_count=total_count,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
        )
    
    async def get_audit_log_by_id(self, audit_log_id: str) -> Optional[AuditLogResponse]:
        """
        查詢稽核日誌詳情
        
        Args:
            audit_log_id: 稽核日誌 ID
        
        Returns:
            AuditLogResponse: 稽核日誌回應，如果不存在則返回 None
        """
        audit_log = await self.repository.get_by_id(audit_log_id)
        
        if not audit_log:
            return None
        
        return self._to_response(audit_log)
    
    def _to_response(self, audit_log: AuditLog) -> AuditLogResponse:
        """
        將領域模型轉換為回應格式
        
        Args:
            audit_log: 稽核日誌實體
        
        Returns:
            AuditLogResponse: 稽核日誌回應
        """
        return AuditLogResponse(
            id=audit_log.id,
            user_id=audit_log.user_id,
            action=audit_log.action,
            resource_type=audit_log.resource_type,
            resource_id=audit_log.resource_id,
            details=audit_log.details,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent,
            created_at=audit_log.created_at,
        )

