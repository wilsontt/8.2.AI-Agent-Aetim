"""
通知規則聚合根

通知規則聚合根包含所有業務邏輯方法，負責維護通知規則的一致性。
"""

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, time
import uuid

from ..value_objects.notification_type import NotificationType
from ..domain_events.notification_rule_updated_event import NotificationRuleUpdatedEvent


@dataclass
class NotificationRule:
    """
    通知規則聚合根
    
    聚合根負責：
    1. 維護聚合的一致性邊界
    2. 實作業務邏輯
    3. 發布領域事件
    
    業務規則：
    - 通知類型必須為有效的 NotificationType（AC-021-1）
    - 風險分數閾值必須 ≥ 0.0 且 ≤ 10.0（AC-021-1）
    - 收件人清單不能為空（AC-021-2）
    """
    
    id: str
    notification_type: NotificationType
    is_enabled: bool
    recipients: List[str]
    risk_score_threshold: Optional[float] = None
    send_time: Optional[time] = None
    _domain_events: list = field(default_factory=list, repr=False)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    updated_by: str = "system"
    
    def __post_init__(self):
        """驗證聚合根的有效性"""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not isinstance(self.notification_type, NotificationType):
            raise ValueError(f"無效的通知類型: {self.notification_type}")
        
        if not self.recipients or len(self.recipients) == 0:
            raise ValueError("收件人清單不能為空")
        
        if self.risk_score_threshold is not None:
            if self.risk_score_threshold < 0.0 or self.risk_score_threshold > 10.0:
                raise ValueError("風險分數閾值必須在 0.0 到 10.0 之間")
    
    @classmethod
    def create(
        cls,
        notification_type: NotificationType,
        recipients: List[str],
        risk_score_threshold: Optional[float] = None,
        send_time: Optional[time] = None,
        is_enabled: bool = True,
        created_by: str = "system",
    ) -> "NotificationRule":
        """
        建立通知規則（工廠方法，AC-021-1）
        
        Args:
            notification_type: 通知類型
            recipients: 收件人清單
            risk_score_threshold: 風險分數閾值（可選，如果不提供則使用預設值）
            send_time: 發送時間（可選）
            is_enabled: 是否啟用（預設：True）
            created_by: 建立者（預設：system）
        
        Returns:
            NotificationRule: 新建立的通知規則聚合根
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        # 如果未提供風險分數閾值，使用預設值
        if risk_score_threshold is None:
            risk_score_threshold = notification_type.get_default_risk_threshold()
        
        rule = cls(
            id=str(uuid.uuid4()),
            notification_type=notification_type,
            is_enabled=is_enabled,
            recipients=recipients,
            risk_score_threshold=risk_score_threshold,
            send_time=send_time,
            created_by=created_by,
        )
        
        return rule
    
    def should_trigger(self, risk_score: Optional[float] = None) -> bool:
        """
        檢查是否應該觸發通知（AC-021-1）
        
        Args:
            risk_score: 風險分數（可選）
        
        Returns:
            bool: 是否應該觸發通知
        """
        if not self.is_enabled:
            return False
        
        # 週報通知由排程觸發，不需要風險分數
        if self.notification_type == NotificationType.WEEKLY:
            return True
        
        # 嚴重威脅通知和高風險每日摘要需要風險分數
        if risk_score is None or self.risk_score_threshold is None:
            return False
        
        return risk_score >= self.risk_score_threshold
    
    def toggle_enabled(self, updated_by: str = "system") -> None:
        """
        啟用/停用通知（AC-021-3）
        
        Args:
            updated_by: 更新者（預設：system）
        """
        self.is_enabled = not self.is_enabled
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
        
        # 發布領域事件
        self._publish_domain_event(
            NotificationRuleUpdatedEvent(
                rule_id=self.id,
                notification_type=self.notification_type,
                updated_at=self.updated_at,
                updated_by=updated_by,
            )
        )
    
    def update_recipients(
        self,
        recipients: List[str],
        updated_by: str = "system",
    ) -> None:
        """
        更新收件人（AC-021-2）
        
        Args:
            recipients: 新收件人清單
            updated_by: 更新者（預設：system）
        
        Raises:
            ValueError: 當收件人清單為空時
        """
        if not recipients or len(recipients) == 0:
            raise ValueError("收件人清單不能為空")
        
        self.recipients = recipients
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
        
        # 發布領域事件
        self._publish_domain_event(
            NotificationRuleUpdatedEvent(
                rule_id=self.id,
                notification_type=self.notification_type,
                updated_at=self.updated_at,
                updated_by=updated_by,
            )
        )
    
    def update_risk_threshold(
        self,
        risk_score_threshold: Optional[float],
        updated_by: str = "system",
    ) -> None:
        """
        更新風險分數閾值
        
        Args:
            risk_score_threshold: 新風險分數閾值
            updated_by: 更新者（預設：system）
        
        Raises:
            ValueError: 當風險分數閾值無效時
        """
        if risk_score_threshold is not None:
            if risk_score_threshold < 0.0 or risk_score_threshold > 10.0:
                raise ValueError("風險分數閾值必須在 0.0 到 10.0 之間")
        
        self.risk_score_threshold = risk_score_threshold
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
        
        # 發布領域事件
        self._publish_domain_event(
            NotificationRuleUpdatedEvent(
                rule_id=self.id,
                notification_type=self.notification_type,
                updated_at=self.updated_at,
                updated_by=updated_by,
            )
        )
    
    def _publish_domain_event(self, event: any) -> None:
        """
        發布領域事件
        
        Args:
            event: 領域事件
        """
        if not hasattr(self, "_domain_events"):
            self._domain_events = []
        
        self._domain_events.append(event)
    
    def get_domain_events(self) -> list:
        """
        取得所有領域事件
        
        Returns:
            list: 領域事件清單
        """
        return getattr(self, "_domain_events", [])
    
    def clear_domain_events(self) -> None:
        """清除所有領域事件"""
        self._domain_events = []

