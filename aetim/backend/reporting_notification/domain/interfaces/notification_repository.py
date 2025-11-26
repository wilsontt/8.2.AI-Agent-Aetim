"""
通知 Repository 介面

定義通知資料存取的抽象介面。
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..aggregates.notification import Notification


class INotificationRepository(ABC):
    """
    通知 Repository 介面
    
    定義通知資料存取操作的抽象介面。
    """
    
    @abstractmethod
    async def save(self, notification: Notification) -> None:
        """
        儲存通知
        
        Args:
            notification: 通知聚合根
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """
        依 ID 查詢通知
        
        Args:
            notification_id: 通知 ID
        
        Returns:
            Optional[Notification]: 通知聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_by_threat_id(self, threat_id: str) -> List[Notification]:
        """
        依威脅 ID 查詢通知
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            List[Notification]: 通知聚合根清單
        """
        pass
    
    @abstractmethod
    async def get_by_report_id(self, report_id: str) -> List[Notification]:
        """
        依報告 ID 查詢通知
        
        Args:
            report_id: 報告 ID
        
        Returns:
            List[Notification]: 通知聚合根清單
        """
        pass

