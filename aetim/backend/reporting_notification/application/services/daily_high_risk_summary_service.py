"""
每日高風險威脅摘要服務（Application Layer）

負責生成和發送每日高風險威脅摘要。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

from ...domain.value_objects.notification_type import NotificationType
from ...domain.interfaces.notification_rule_repository import INotificationRuleRepository
from ...application.services.notification_service import NotificationService
from analysis_assessment.domain.interfaces.risk_assessment_repository import (
    IRiskAssessmentRepository,
)
from analysis_assessment.domain.aggregates.risk_assessment import RiskAssessment
from threat_intelligence.domain.interfaces.threat_repository import IThreatRepository
from threat_intelligence.domain.aggregates.threat import Threat
from asset_management.domain.interfaces.asset_repository import IAssetRepository
from asset_management.domain.aggregates.asset import Asset

logger = structlog.get_logger(__name__)


class DailyHighRiskSummaryService:
    """
    每日高風險威脅摘要服務
    
    負責：
    1. 生成每日高風險威脅摘要（AC-020-1）
    2. 發送摘要通知（AC-020-3）
    """
    
    def __init__(
        self,
        risk_assessment_repository: IRiskAssessmentRepository,
        threat_repository: IThreatRepository,
        asset_repository: IAssetRepository,
        notification_rule_repository: INotificationRuleRepository,
        notification_service: NotificationService,
    ):
        """
        初始化每日高風險威脅摘要服務
        
        Args:
            risk_assessment_repository: 風險評估 Repository
            threat_repository: 威脅 Repository
            asset_repository: 資產 Repository
            notification_rule_repository: 通知規則 Repository
            notification_service: 通知服務
        """
        self.risk_assessment_repository = risk_assessment_repository
        self.threat_repository = threat_repository
        self.asset_repository = asset_repository
        self.notification_rule_repository = notification_rule_repository
        self.notification_service = notification_service
    
    async def generate_summary(
        self,
        date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        生成每日高風險威脅摘要（AC-020-1）
        
        Args:
            date: 日期（可選，預設為今天）
        
        Returns:
            Dict[str, Any]: 摘要內容，包含：
                - threat_count: 威脅數量
                - threats: 威脅清單
                - total_affected_assets: 受影響資產總數
                - average_risk_score: 平均風險分數
                - asset_statistics: 受影響資產統計
        """
        if date is None:
            date = datetime.utcnow()
        
        # 計算日期範圍（當天的開始和結束）
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        logger.info(
            "開始生成每日高風險威脅摘要",
            date=date.strftime("%Y-%m-%d"),
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        
        # 查詢本日高風險威脅（風險分數 ≥ 6.0，AC-020-1）
        risk_assessments = await self.risk_assessment_repository.get_by_risk_score_range(
            min_risk_score=6.0,
            max_risk_score=None,
            start_date=start_date,
            end_date=end_date,
        )
        
        logger.info(
            "查詢到高風險威脅",
            count=len(risk_assessments),
            date=date.strftime("%Y-%m-%d"),
        )
        
        # 統計威脅數量（AC-020-2）
        threat_count = len(risk_assessments)
        
        # 生成威脅清單（AC-020-2）
        threats = []
        total_affected_assets = 0
        total_risk_score = 0.0
        
        for assessment in risk_assessments:
            # 取得威脅資訊
            threat = await self.threat_repository.get_by_id(assessment.threat_id)
            if not threat:
                continue
            
            threats.append({
                "threat_id": assessment.threat_id,
                "title": threat.title or "未知威脅",
                "cve_id": threat.cve_id or "N/A",
                "risk_score": assessment.final_risk_score,
                "risk_level": assessment.risk_level,
                "affected_assets_count": assessment.affected_asset_count,
            })
            
            total_affected_assets += assessment.affected_asset_count
            total_risk_score += assessment.final_risk_score
        
        # 計算平均風險分數
        average_risk_score = (
            total_risk_score / threat_count if threat_count > 0 else 0.0
        )
        
        # 統計受影響資產（AC-020-2）
        asset_statistics = await self._calculate_asset_statistics(risk_assessments)
        
        summary = {
            "threat_count": threat_count,
            "threats": threats,
            "total_affected_assets": total_affected_assets,
            "average_risk_score": round(average_risk_score, 2),
            "asset_statistics": asset_statistics,
            "date": date.strftime("%Y-%m-%d"),
        }
        
        logger.info(
            "每日高風險威脅摘要生成完成",
            threat_count=threat_count,
            total_affected_assets=total_affected_assets,
            average_risk_score=average_risk_score,
        )
        
        return summary
    
    async def send_summary(
        self,
        date: Optional[datetime] = None,
    ) -> None:
        """
        發送每日高風險威脅摘要（AC-020-3）
        
        Args:
            date: 日期（可選，預設為今天）
        """
        try:
            # 取得啟用的高風險每日摘要通知規則
            notification_rule = await self.notification_rule_repository.get_by_type(
                NotificationType.HIGH_RISK_DAILY
            )
            
            if not notification_rule:
                logger.warning("找不到啟用的高風險每日摘要通知規則")
                return
            
            if not notification_rule.is_enabled:
                logger.debug("高風險每日摘要通知規則已停用")
                return
            
            # 生成摘要
            summary = await self.generate_summary(date)
            
            # 發送通知
            notification = await self.notification_service.send_notification(
                notification_rule=notification_rule,
                content=summary,
            )
            
            logger.info(
                "每日高風險威脅摘要已發送",
                notification_id=notification.id,
                threat_count=summary["threat_count"],
                recipients=notification.recipients,
            )
            
        except Exception as e:
            logger.error(
                "發送每日高風險威脅摘要失敗",
                date=date.strftime("%Y-%m-%d") if date else None,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def _calculate_asset_statistics(
        self,
        risk_assessments: List[RiskAssessment],
    ) -> List[Dict[str, Any]]:
        """
        計算受影響資產統計
        
        Args:
            risk_assessments: 風險評估清單
        
        Returns:
            List[Dict[str, Any]]: 資產統計清單
        """
        # TODO: 實作資產統計邏輯
        # 目前先返回空清單，未來可整合威脅-資產關聯服務
        return []

