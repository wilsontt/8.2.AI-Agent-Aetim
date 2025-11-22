"""
稽核日誌 Repository 介面

定義 AuditLog Repository 的抽象介面，實作將在 Infrastructure Layer。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..entities.audit_log import AuditLog


class IAuditLogRepository(ABC):
    """
    稽核日誌 Repository 介面
    
    定義稽核日誌的持久化操作，實作將在 Infrastructure Layer。
    """
    
    @abstractmethod
    async def save(self, audit_log: AuditLog) -> None:
        """
        儲存稽核日誌（僅新增，不可修改）
        
        業務規則：稽核日誌不可篡改（寫入後不可修改）
        
        Args:
            audit_log: 稽核日誌實體
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, audit_log_id: str) -> Optional[AuditLog]:
        """
        依 ID 查詢稽核日誌
        
        Args:
            audit_log_id: 稽核日誌 ID
        
        Returns:
            AuditLog: 稽核日誌實體，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_by_filters(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> tuple[List[AuditLog], int]:
        """
        依條件查詢稽核日誌（支援多種篩選條件和分頁）
        
        Args:
            user_id: 使用者 ID（可選）
            action: 操作類型（可選）
            resource_type: 資源類型（可選）
            resource_id: 資源 ID（可選）
            start_date: 開始日期（可選）
            end_date: 結束日期（可選）
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20）
            sort_by: 排序欄位（created_at 等）
            sort_order: 排序方向（asc、desc）
        
        Returns:
            tuple[List[AuditLog], int]: (稽核日誌清單, 總筆數)
        """
        pass

