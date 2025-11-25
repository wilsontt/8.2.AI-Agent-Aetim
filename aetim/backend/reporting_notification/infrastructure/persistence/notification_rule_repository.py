"""
通知規則 Repository 實作

實作通知規則的資料存取邏輯。
"""

import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from ...domain.interfaces.notification_rule_repository import INotificationRuleRepository
from ...domain.aggregates.notification_rule import NotificationRule
from ...domain.value_objects.notification_type import NotificationType
from .models import NotificationRule as NotificationRuleModel

logger = structlog.get_logger(__name__)


class NotificationRuleRepository(INotificationRuleRepository):
    """
    通知規則 Repository 實作
    
    負責通知規則的資料存取。
    """
    
    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 資料庫會話
        """
        self.session = session
    
    async def save(self, rule: NotificationRule) -> None:
        """
        儲存通知規則
        
        Args:
            rule: 通知規則聚合根
        """
        try:
            # 檢查規則是否存在
            stmt = select(NotificationRuleModel).where(NotificationRuleModel.id == rule.id)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            # 準備收件人 JSON
            recipients_json = json.dumps(rule.recipients, ensure_ascii=False)
            
            if existing:
                # 更新現有規則
                existing.notification_type = rule.notification_type.value
                existing.is_enabled = rule.is_enabled
                existing.risk_score_threshold = rule.risk_score_threshold
                existing.send_time = rule.send_time
                existing.recipients = recipients_json
                existing.updated_at = rule.updated_at
                existing.updated_by = rule.updated_by
            else:
                # 新增規則
                new_rule = NotificationRuleModel(
                    id=rule.id,
                    notification_type=rule.notification_type.value,
                    is_enabled=rule.is_enabled,
                    risk_score_threshold=rule.risk_score_threshold,
                    send_time=rule.send_time,
                    recipients=recipients_json,
                    created_at=rule.created_at,
                    updated_at=rule.updated_at,
                    created_by=rule.created_by,
                    updated_by=rule.updated_by,
                )
                self.session.add(new_rule)
            
            await self.session.flush()
            
            logger.info(
                "通知規則已儲存",
                rule_id=rule.id,
                notification_type=rule.notification_type.value,
            )
            
        except Exception as e:
            logger.error(
                "儲存通知規則失敗",
                rule_id=rule.id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_by_id(self, rule_id: str) -> Optional[NotificationRule]:
        """
        依 ID 查詢通知規則
        
        Args:
            rule_id: 通知規則 ID
        
        Returns:
            Optional[NotificationRule]: 通知規則聚合根，如果不存在則返回 None
        """
        try:
            stmt = select(NotificationRuleModel).where(NotificationRuleModel.id == rule_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._to_domain(model)
            
        except Exception as e:
            logger.error(
                "查詢通知規則失敗",
                rule_id=rule_id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_all(self) -> List[NotificationRule]:
        """
        查詢所有通知規則
        
        Returns:
            List[NotificationRule]: 通知規則聚合根清單
        """
        try:
            stmt = select(NotificationRuleModel)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_domain(model) for model in models]
            
        except Exception as e:
            logger.error(
                "查詢所有通知規則失敗",
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_enabled_rules(self) -> List[NotificationRule]:
        """
        查詢啟用的通知規則
        
        Returns:
            List[NotificationRule]: 啟用的通知規則聚合根清單
        """
        try:
            stmt = select(NotificationRuleModel).where(NotificationRuleModel.is_enabled == True)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_domain(model) for model in models]
            
        except Exception as e:
            logger.error(
                "查詢啟用的通知規則失敗",
                error=str(e),
                exc_info=True,
            )
            raise
    
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
        try:
            stmt = select(NotificationRuleModel).where(
                NotificationRuleModel.notification_type == notification_type.value
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._to_domain(model)
            
        except Exception as e:
            logger.error(
                "依類型查詢通知規則失敗",
                notification_type=notification_type.value,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def delete(self, rule_id: str) -> None:
        """
        刪除通知規則
        
        Args:
            rule_id: 通知規則 ID
        """
        try:
            stmt = select(NotificationRuleModel).where(NotificationRuleModel.id == rule_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                await self.session.delete(model)
                await self.session.flush()
                
                logger.info(
                    "通知規則已刪除",
                    rule_id=rule_id,
                )
            else:
                logger.warning(
                    "嘗試刪除不存在的通知規則",
                    rule_id=rule_id,
                )
            
        except Exception as e:
            logger.error(
                "刪除通知規則失敗",
                rule_id=rule_id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    def _to_domain(self, model: NotificationRuleModel) -> NotificationRule:
        """
        將資料庫模型轉換為領域模型
        
        Args:
            model: 資料庫模型
        
        Returns:
            NotificationRule: 領域模型
        """
        # 解析收件人 JSON
        recipients = []
        if model.recipients:
            try:
                recipients = json.loads(model.recipients)
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "無法解析通知規則收件人 JSON",
                    rule_id=model.id,
                )
        
        # 建立領域模型
        rule = NotificationRule(
            id=model.id,
            notification_type=NotificationType.from_string(model.notification_type),
            is_enabled=model.is_enabled,
            recipients=recipients,
            risk_score_threshold=float(model.risk_score_threshold) if model.risk_score_threshold else None,
            send_time=model.send_time,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
        )
        
        return rule

