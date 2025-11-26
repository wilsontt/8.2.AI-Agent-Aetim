"""
通知 Repository 實作

實作通知的資料存取邏輯。
"""

import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from ...domain.interfaces.notification_repository import INotificationRepository
from ...domain.aggregates.notification import Notification
from ...domain.value_objects.notification_type import NotificationType
from .models import Notification as NotificationModel

logger = structlog.get_logger(__name__)


class NotificationRepository(INotificationRepository):
    """
    通知 Repository 實作
    
    負責通知的資料存取。
    """
    
    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 資料庫會話
        """
        self.session = session
    
    async def save(self, notification: Notification) -> None:
        """
        儲存通知
        
        Args:
            notification: 通知聚合根
        """
        try:
            # 檢查通知是否存在
            stmt = select(NotificationModel).where(NotificationModel.id == notification.id)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            # 準備收件人 JSON
            recipients_json = json.dumps(notification.recipients, ensure_ascii=False)
            
            if existing:
                # 更新現有通知
                existing.notification_type = notification.notification_type.value
                existing.recipients = recipients_json
                existing.subject = notification.subject
                existing.body = notification.body
                existing.notification_rule_id = notification.notification_rule_id
                existing.related_threat_id = notification.related_threat_id
                existing.related_report_id = notification.related_report_id
                existing.sent_at = notification.sent_at
                existing.status = notification.status
                existing.error_message = notification.error_message
            else:
                # 新增通知
                new_notification = NotificationModel(
                    id=notification.id,
                    notification_type=notification.notification_type.value,
                    recipients=recipients_json,
                    subject=notification.subject,
                    body=notification.body,
                    notification_rule_id=notification.notification_rule_id,
                    related_threat_id=notification.related_threat_id,
                    related_report_id=notification.related_report_id,
                    sent_at=notification.sent_at,
                    status=notification.status,
                    error_message=notification.error_message,
                )
                self.session.add(new_notification)
            
            await self.session.flush()
            
            logger.info(
                "通知已儲存",
                notification_id=notification.id,
                notification_type=notification.notification_type.value,
                status=notification.status,
            )
            
        except Exception as e:
            logger.error(
                "儲存通知失敗",
                notification_id=notification.id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """
        依 ID 查詢通知
        
        Args:
            notification_id: 通知 ID
        
        Returns:
            Optional[Notification]: 通知聚合根，如果不存在則返回 None
        """
        try:
            stmt = select(NotificationModel).where(NotificationModel.id == notification_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._to_domain(model)
            
        except Exception as e:
            logger.error(
                "查詢通知失敗",
                notification_id=notification_id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_by_threat_id(self, threat_id: str) -> List[Notification]:
        """
        依威脅 ID 查詢通知
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            List[Notification]: 通知聚合根清單
        """
        try:
            stmt = select(NotificationModel).where(
                NotificationModel.related_threat_id == threat_id
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_domain(model) for model in models]
            
        except Exception as e:
            logger.error(
                "依威脅 ID 查詢通知失敗",
                threat_id=threat_id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_by_report_id(self, report_id: str) -> List[Notification]:
        """
        依報告 ID 查詢通知
        
        Args:
            report_id: 報告 ID
        
        Returns:
            List[Notification]: 通知聚合根清單
        """
        try:
            stmt = select(NotificationModel).where(
                NotificationModel.related_report_id == report_id
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_domain(model) for model in models]
            
        except Exception as e:
            logger.error(
                "依報告 ID 查詢通知失敗",
                report_id=report_id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    def _to_domain(self, model: NotificationModel) -> Notification:
        """
        將資料庫模型轉換為領域模型
        
        Args:
            model: 資料庫模型
        
        Returns:
            Notification: 領域模型
        """
        # 解析收件人 JSON
        recipients = []
        if model.recipients:
            try:
                recipients = json.loads(model.recipients)
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "無法解析通知收件人 JSON",
                    notification_id=model.id,
                )
        
        # 建立領域模型
        notification = Notification(
            id=model.id,
            notification_type=NotificationType.from_string(model.notification_type),
            recipients=recipients,
            subject=model.subject,
            body=model.body,
            notification_rule_id=model.notification_rule_id,
            related_threat_id=model.related_threat_id,
            related_report_id=model.related_report_id,
            sent_at=model.sent_at,
            status=model.status,
            error_message=model.error_message,
            created_at=model.created_at if hasattr(model, "created_at") else None,
        )
        
        return notification

