"""
通知規則服務（Application Layer）

協調通知規則管理流程，整合 Domain Service 和 Infrastructure。
"""

from typing import List, Optional
from datetime import time
import structlog

from ...domain.aggregates.notification_rule import NotificationRule
from ...domain.value_objects.notification_type import NotificationType
from ...domain.interfaces.notification_rule_repository import INotificationRuleRepository
from typing import TYPE_CHECKING, Any
from datetime import datetime

if TYPE_CHECKING:
    from system_management.application.services.audit_log_service import AuditLogService

logger = structlog.get_logger(__name__)


class NotificationRuleService:
    """
    通知規則服務（Application Layer）
    
    負責協調通知規則管理流程，整合：
    1. Domain Service（通知規則業務邏輯）
    2. Infrastructure（Repository、稽核日誌）
    """
    
    def __init__(
        self,
        repository: INotificationRuleRepository,
        audit_log_service: Optional[Any] = None,  # AuditLogService，使用 Any 避免循環導入
    ):
        """
        初始化通知規則服務
        
        Args:
            repository: 通知規則 Repository
            audit_log_service: 稽核日誌服務（可選）
        """
        self.repository = repository
        self.audit_log_service = audit_log_service
    
    async def create_rule(
        self,
        notification_type: NotificationType,
        recipients: List[str],
        risk_score_threshold: Optional[float] = None,
        send_time: Optional[time] = None,
        is_enabled: bool = True,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> NotificationRule:
        """
        建立通知規則（AC-021-1）
        
        Args:
            notification_type: 通知類型
            recipients: 收件人清單
            risk_score_threshold: 風險分數閾值（可選）
            send_time: 發送時間（可選）
            is_enabled: 是否啟用（預設：True）
            user_id: 使用者 ID（用於稽核日誌）
            ip_address: IP 位址（用於稽核日誌）
            user_agent: User Agent（用於稽核日誌）
        
        Returns:
            NotificationRule: 新建立的通知規則聚合根
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        # 建立通知規則
        rule = NotificationRule.create(
            notification_type=notification_type,
            recipients=recipients,
            risk_score_threshold=risk_score_threshold,
            send_time=send_time,
            is_enabled=is_enabled,
            created_by=user_id or "system",
        )
        
        # 儲存到資料庫
        await self.repository.save(rule)
        
        # 記錄稽核日誌（AC-021-4）
        if self.audit_log_service:
            try:
                await self.audit_log_service.log_action(
                    user_id=user_id,
                    action="CREATE",
                    resource_type="NotificationRule",
                    resource_id=rule.id,
                    details={
                        "notification_type": notification_type.value,
                        "recipients": recipients,
                        "risk_score_threshold": risk_score_threshold,
                        "is_enabled": is_enabled,
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            except Exception as e:
                logger.warning(
                    "記錄稽核日誌失敗",
                    rule_id=rule.id,
                    error=str(e),
                )
        
        logger.info(
            "通知規則已建立",
            rule_id=rule.id,
            notification_type=notification_type.value,
        )
        
        return rule
    
    async def update_rule(
        self,
        rule_id: str,
        recipients: Optional[List[str]] = None,
        risk_score_threshold: Optional[float] = None,
        send_time: Optional[time] = None,
        is_enabled: Optional[bool] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> NotificationRule:
        """
        更新通知規則（AC-021-2, AC-021-3）
        
        Args:
            rule_id: 通知規則 ID
            recipients: 新收件人清單（可選）
            risk_score_threshold: 新風險分數閾值（可選）
            send_time: 新發送時間（可選）
            is_enabled: 新啟用狀態（可選）
            user_id: 使用者 ID（用於稽核日誌）
            ip_address: IP 位址（用於稽核日誌）
            user_agent: User Agent（用於稽核日誌）
        
        Returns:
            NotificationRule: 更新後的通知規則聚合根
        
        Raises:
            ValueError: 當通知規則不存在或輸入參數無效時
        """
        # 取得通知規則
        rule = await self.repository.get_by_id(rule_id)
        if not rule:
            raise ValueError(f"找不到通知規則：{rule_id}")
        
        # 記錄變更詳情（用於稽核日誌）
        changes = {}
        
        # 更新收件人（AC-021-2）
        if recipients is not None:
            old_recipients = rule.recipients.copy()
            rule.update_recipients(recipients, updated_by=user_id or "system")
            changes["recipients"] = {"old": old_recipients, "new": recipients}
        
        # 更新風險分數閾值
        if risk_score_threshold is not None:
            old_threshold = rule.risk_score_threshold
            rule.update_risk_threshold(risk_score_threshold, updated_by=user_id or "system")
            changes["risk_score_threshold"] = {"old": old_threshold, "new": risk_score_threshold}
        
        # 更新發送時間
        if send_time is not None:
            old_send_time = rule.send_time
            rule.send_time = send_time
            rule.updated_at = datetime.utcnow()
            rule.updated_by = user_id or "system"
            changes["send_time"] = {"old": old_send_time, "new": send_time}
        
        # 更新啟用狀態（AC-021-3）
        if is_enabled is not None and is_enabled != rule.is_enabled:
            old_enabled = rule.is_enabled
            rule.toggle_enabled(updated_by=user_id or "system")
            changes["is_enabled"] = {"old": old_enabled, "new": rule.is_enabled}
        
        # 儲存到資料庫
        await self.repository.save(rule)
        
        # 記錄稽核日誌（AC-021-4）
        if self.audit_log_service and changes:
            try:
                await self.audit_log_service.log_action(
                    user_id=user_id,
                    action="UPDATE",
                    resource_type="NotificationRule",
                    resource_id=rule_id,
                    details=changes,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            except Exception as e:
                logger.warning(
                    "記錄稽核日誌失敗",
                    rule_id=rule_id,
                    error=str(e),
                )
        
        logger.info(
            "通知規則已更新",
            rule_id=rule_id,
            changes=list(changes.keys()),
        )
        
        return rule
    
    async def delete_rule(
        self,
        rule_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        刪除通知規則
        
        Args:
            rule_id: 通知規則 ID
            user_id: 使用者 ID（用於稽核日誌）
            ip_address: IP 位址（用於稽核日誌）
            user_agent: User Agent（用於稽核日誌）
        
        Raises:
            ValueError: 當通知規則不存在時
        """
        # 取得通知規則（用於稽核日誌）
        rule = await self.repository.get_by_id(rule_id)
        if not rule:
            raise ValueError(f"找不到通知規則：{rule_id}")
        
        # 刪除規則
        await self.repository.delete(rule_id)
        
        # 記錄稽核日誌（AC-021-4）
        if self.audit_log_service:
            try:
                await self.audit_log_service.log_action(
                    user_id=user_id,
                    action="DELETE",
                    resource_type="NotificationRule",
                    resource_id=rule_id,
                    details={
                        "notification_type": rule.notification_type.value,
                        "recipients": rule.recipients,
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            except Exception as e:
                logger.warning(
                    "記錄稽核日誌失敗",
                    rule_id=rule_id,
                    error=str(e),
                )
        
        logger.info(
            "通知規則已刪除",
            rule_id=rule_id,
        )
    
    async def get_rules(self) -> List[NotificationRule]:
        """
        查詢通知規則清單
        
        Returns:
            List[NotificationRule]: 通知規則聚合根清單
        """
        return await self.repository.get_all()
    
    async def get_rule_by_id(self, rule_id: str) -> Optional[NotificationRule]:
        """
        依 ID 查詢通知規則
        
        Args:
            rule_id: 通知規則 ID
        
        Returns:
            Optional[NotificationRule]: 通知規則聚合根，如果不存在則返回 None
        """
        return await self.repository.get_by_id(rule_id)
    
    async def get_rule_by_type(
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
        return await self.repository.get_by_type(notification_type)
    
    async def get_enabled_rules(self) -> List[NotificationRule]:
        """
        查詢啟用的通知規則
        
        Returns:
            List[NotificationRule]: 啟用的通知規則聚合根清單
        """
        return await self.repository.get_enabled_rules()

