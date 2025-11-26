"""
通知聚合根

通知聚合根包含所有業務邏輯方法，負責維護通知的一致性。
"""

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from ..value_objects.notification_type import NotificationType


@dataclass
class Notification:
    """
    通知聚合根
    
    聚合根負責：
    1. 維護聚合的一致性邊界
    2. 實作業務邏輯
    3. 發布領域事件
    """
    
    id: str
    notification_type: NotificationType
    recipients: List[str]
    subject: str
    body: str
    notification_rule_id: Optional[str] = None
    related_threat_id: Optional[str] = None
    related_report_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    status: str = "Pending"  # Pending, Sent, Failed
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """驗證聚合根的有效性"""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not isinstance(self.notification_type, NotificationType):
            raise ValueError(f"無效的通知類型: {self.notification_type}")
        
        if not self.recipients or len(self.recipients) == 0:
            raise ValueError("收件人清單不能為空")
        
        if not self.subject:
            raise ValueError("主旨不能為空")
        
        if not self.body:
            raise ValueError("內容不能為空")
        
        if self.status not in ["Pending", "Sent", "Failed"]:
            raise ValueError(f"無效的狀態: {self.status}")
    
    @classmethod
    def create(
        cls,
        notification_type: NotificationType,
        recipients: List[str],
        subject: str,
        body: str,
        notification_rule_id: Optional[str] = None,
        related_threat_id: Optional[str] = None,
        related_report_id: Optional[str] = None,
    ) -> "Notification":
        """
        建立通知（工廠方法）
        
        Args:
            notification_type: 通知類型
            recipients: 收件人清單
            subject: 主旨
            body: 內容
            notification_rule_id: 通知規則 ID（可選）
            related_threat_id: 相關威脅 ID（可選）
            related_report_id: 相關報告 ID（可選）
        
        Returns:
            Notification: 新建立的通知聚合根
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        return cls(
            id=str(uuid.uuid4()),
            notification_type=notification_type,
            recipients=recipients,
            subject=subject,
            body=body,
            notification_rule_id=notification_rule_id,
            related_threat_id=related_threat_id,
            related_report_id=related_report_id,
            status="Pending",
        )
    
    def mark_as_sent(self) -> None:
        """
        標記為已發送
        
        更新狀態為 Sent，並記錄發送時間。
        """
        self.status = "Sent"
        self.sent_at = datetime.utcnow()
        self.error_message = None
    
    def mark_as_failed(self, error_message: str) -> None:
        """
        標記為發送失敗
        
        Args:
            error_message: 錯誤訊息
        """
        self.status = "Failed"
        self.sent_at = datetime.utcnow()
        self.error_message = error_message

