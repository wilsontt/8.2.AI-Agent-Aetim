"""
通知規則更新事件

當通知規則變更時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime
from ..value_objects.notification_type import NotificationType


@dataclass(frozen=True)
class NotificationRuleUpdatedEvent:
    """通知規則更新事件"""
    
    rule_id: str
    notification_type: NotificationType
    updated_at: datetime
    updated_by: str | None = None  # 更新者（可選）
    
    def __str__(self) -> str:
        return (
            f"NotificationRuleUpdatedEvent(rule_id='{self.rule_id}', "
            f"notification_type='{self.notification_type.value}', "
            f"updated_at='{self.updated_at.isoformat()}')"
        )

