"""
通知規則 Repository 介面

定義通知規則資料存取的抽象介面。
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..aggregates.notification_rule import NotificationRule
from ..value_objects.notification_type import NotificationType


class INotificationRuleRepository(ABC):
    """
    通知規則 Repository 介面
    
    定義通知規則資料存取操作的抽象介面。
    """
    
    @abstractmethod
    async def save(self, rule: NotificationRule) -> None:
        """
        儲存通知規則
        
        Args:
            rule: 通知規則聚合根
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, rule_id: str) -> Optional[NotificationRule]:
        """
        依 ID 查詢通知規則
        
        Args:
            rule_id: 通知規則 ID
        
        Returns:
            Optional[NotificationRule]: 通知規則聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_all(self) -> List[NotificationRule]:
        """
        查詢所有通知規則
        
        Returns:
            List[NotificationRule]: 通知規則聚合根清單
        """
        pass
    
    @abstractmethod
    async def get_enabled_rules(self) -> List[NotificationRule]:
        """
        查詢啟用的通知規則
        
        Returns:
            List[NotificationRule]: 啟用的通知規則聚合根清單
        """
        pass
    
    @abstractmethod
    async def get_by_type(
        self,
        notification_type: NotificationType,
    ) -> Optional[NotificationRule]:
        """
        依類型查詢通知規則
        
        Args:
            notification_type: 通知類型
        
        Returns:
            Optional[NotificationRule]: 通知規則聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def delete(self, rule_id: str) -> None:
        """
        刪除通知規則
        
        Args:
            rule_id: 通知規則 ID
        """
        pass

