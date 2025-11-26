"""
風險評估事件處理器

處理 RiskAssessmentCompleted 事件，當風險評估完成時發送嚴重威脅通知。
"""

from typing import Optional
import structlog

from analysis_assessment.domain.domain_events.risk_assessment_completed_event import (
    RiskAssessmentCompletedEvent,
)
from ...domain.value_objects.notification_type import NotificationType
from ...domain.interfaces.notification_rule_repository import INotificationRuleRepository
from ...application.services.notification_service import NotificationService
from threat_intelligence.domain.interfaces.threat_repository import IThreatRepository
from threat_intelligence.domain.aggregates.threat import Threat
from asset_management.domain.interfaces.asset_repository import IAssetRepository
from asset_management.domain.aggregates.asset import Asset

logger = structlog.get_logger(__name__)


class RiskAssessmentEventHandler:
    """
    風險評估事件處理器
    
    訂閱 RiskAssessmentCompleted 事件，當風險評估完成時：
    1. 檢查風險分數是否 ≥ 8.0（AC-019-1）
    2. 取得啟用的嚴重威脅通知規則
    3. 生成通知內容（AC-019-2）
    4. 發送 Email 通知（AC-019-3）
    5. 儲存通知記錄（AC-019-4）
    """
    
    def __init__(
        self,
        notification_rule_repository: INotificationRuleRepository,
        notification_service: NotificationService,
        threat_repository: IThreatRepository,
        asset_repository: IAssetRepository,
    ):
        """
        初始化事件處理器
        
        Args:
            notification_rule_repository: 通知規則 Repository
            notification_service: 通知服務
            threat_repository: 威脅 Repository
            asset_repository: 資產 Repository
        """
        self.notification_rule_repository = notification_rule_repository
        self.notification_service = notification_service
        self.threat_repository = threat_repository
        self.asset_repository = asset_repository
    
    async def handle(self, event: RiskAssessmentCompletedEvent) -> None:
        """
        處理風險評估完成事件（AC-019-1）
        
        Args:
            event: 風險評估完成事件
        """
        try:
            # 檢查風險分數是否 ≥ 8.0（AC-019-1）
            if event.final_risk_score < 8.0:
                logger.debug(
                    "風險分數未達嚴重威脅閾值，不發送通知",
                    risk_assessment_id=event.risk_assessment_id,
                    threat_id=event.threat_id,
                    final_risk_score=event.final_risk_score,
                )
                return
            
            logger.info(
                "發現嚴重威脅，準備發送通知",
                risk_assessment_id=event.risk_assessment_id,
                threat_id=event.threat_id,
                final_risk_score=event.final_risk_score,
            )
            
            # 取得啟用的嚴重威脅通知規則
            notification_rule = await self.notification_rule_repository.get_by_type(
                NotificationType.CRITICAL
            )
            
            if not notification_rule:
                logger.warning(
                    "找不到啟用的嚴重威脅通知規則",
                    threat_id=event.threat_id,
                )
                return
            
            if not notification_rule.is_enabled:
                logger.debug(
                    "嚴重威脅通知規則已停用",
                    threat_id=event.threat_id,
                )
                return
            
            # 檢查是否應該觸發通知
            if not notification_rule.should_trigger(risk_score=event.final_risk_score):
                logger.debug(
                    "通知規則觸發條件未滿足",
                    threat_id=event.threat_id,
                    risk_score=event.final_risk_score,
                    threshold=notification_rule.risk_score_threshold,
                )
                return
            
            # 取得威脅資訊
            threat = await self.threat_repository.get_by_id(event.threat_id)
            if not threat:
                logger.error(
                    "找不到威脅資訊",
                    threat_id=event.threat_id,
                )
                return
            
            # 取得受影響的資產清單
            affected_assets = await self._get_affected_assets(event.threat_id)
            
            # 生成通知內容（AC-019-2）
            content = {
                "threat_title": threat.title or "未知威脅",
                "cve_id": threat.cve_id or "N/A",
                "risk_score": event.final_risk_score,
                "affected_assets_count": event.affected_asset_count,
                "affected_assets": [
                    {
                        "name": asset.name,
                        "type": asset.asset_type,
                        "importance": asset.importance,
                    }
                    for asset in affected_assets[:10]  # 最多顯示 10 個資產
                ],
                "threat_id": event.threat_id,
            }
            
            # 發送通知（AC-019-3, AC-019-4）
            notification = await self.notification_service.send_notification(
                notification_rule=notification_rule,
                content=content,
                related_threat_id=event.threat_id,
            )
            
            logger.info(
                "嚴重威脅通知已發送",
                notification_id=notification.id,
                threat_id=event.threat_id,
                risk_score=event.final_risk_score,
                recipients=notification.recipients,
            )
            
        except Exception as e:
            logger.error(
                "處理風險評估完成事件失敗",
                risk_assessment_id=event.risk_assessment_id,
                threat_id=event.threat_id,
                error=str(e),
                exc_info=True,
            )
            # 不重新拋出異常，避免影響其他事件處理器
    
    async def _get_affected_assets(self, threat_id: str) -> list[Asset]:
        """
        取得受影響的資產清單
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            list[Asset]: 受影響的資產清單
        """
        # TODO: 從威脅-資產關聯表查詢受影響的資產
        # 目前先返回空清單，未來可整合威脅-資產關聯服務
        return []

