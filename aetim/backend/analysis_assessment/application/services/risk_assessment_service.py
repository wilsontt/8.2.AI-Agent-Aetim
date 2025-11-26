"""
風險評估應用服務

負責風險評估的業務邏輯協調，包含歷史記錄管理。
"""

from typing import List, Optional
from datetime import datetime

from ...domain.aggregates.risk_assessment import RiskAssessment
from ...domain.domain_services.risk_calculation_service import RiskCalculationService
from ...domain.interfaces.risk_assessment_history_repository import (
    IRiskAssessmentHistoryRepository,
)
from ...domain.interfaces.risk_assessment_repository import IRiskAssessmentRepository
from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.interfaces.threat_repository import IThreatRepository
from threat_intelligence.domain.interfaces.threat_feed_repository import IThreatFeedRepository
from threat_intelligence.infrastructure.persistence.threat_asset_association_repository import (
    ThreatAssetAssociationRepository,
)
from asset_management.domain.aggregates.asset import Asset
from asset_management.domain.interfaces.asset_repository import IAssetRepository
from analysis_assessment.domain.aggregates.pir import PIR
from analysis_assessment.domain.interfaces.pir_repository import IPIRRepository
from analysis_assessment.domain.domain_events.risk_assessment_completed_event import (
    RiskAssessmentCompletedEvent,
)
from shared_kernel.infrastructure.event_bus import get_event_bus
import structlog

logger = structlog.get_logger(__name__)


class RiskAssessmentService:
    """
    風險評估應用服務
    
    負責協調風險評估的業務邏輯，包含：
    1. 計算風險分數
    2. 儲存風險評估
    3. 儲存歷史記錄（AC-012-5, AC-013-3）
    """

    def __init__(
        self,
        risk_calculation_service: RiskCalculationService,
        threat_repository: IThreatRepository,
        threat_feed_repository: IThreatFeedRepository,
        asset_repository: IAssetRepository,
        pir_repository: IPIRRepository,
        risk_assessment_repository: IRiskAssessmentRepository,
        history_repository: IRiskAssessmentHistoryRepository,
        association_repository: ThreatAssetAssociationRepository,
    ):
        """
        初始化風險評估服務
        
        Args:
            risk_calculation_service: 風險計算服務
            threat_repository: 威脅 Repository
            threat_feed_repository: 威脅來源 Repository
            asset_repository: 資產 Repository
            pir_repository: PIR Repository
            risk_assessment_repository: 風險評估 Repository
            history_repository: 歷史記錄 Repository
            association_repository: 威脅-資產關聯 Repository
        """
        self.risk_calculation_service = risk_calculation_service
        self.threat_repository = threat_repository
        self.threat_feed_repository = threat_feed_repository
        self.asset_repository = asset_repository
        self.pir_repository = pir_repository
        self.risk_assessment_repository = risk_assessment_repository
        self.history_repository = history_repository
        self.association_repository = association_repository

    async def calculate_and_save_risk(
        self,
        threat_id: str,
        threat_asset_association_id: str,
    ) -> RiskAssessment:
        """
        計算並儲存風險評估（包含歷史記錄）
        
        Args:
            threat_id: 威脅 ID
            threat_asset_association_id: 威脅資產關聯 ID
        
        Returns:
            RiskAssessment: 風險評估聚合根
        """
        # 1. 取得威脅
        threat = await self.threat_repository.get_by_id(threat_id)
        if not threat:
            raise ValueError(f"威脅不存在：{threat_id}")

        # 2. 取得威脅來源名稱
        threat_feed_name = None
        if threat.threat_feed_id:
            threat_feed = await self.threat_feed_repository.get_by_id(threat.threat_feed_id)
            if threat_feed:
                threat_feed_name = threat_feed.name

        # 3. 取得受影響的資產
        associated_assets = await self._get_associated_assets(threat_id)

        # 4. 取得啟用的 PIRs
        pirs = await self.pir_repository.get_all_enabled()

        # 5. 計算風險評估
        risk_assessment = self.risk_calculation_service.calculate_risk(
            threat=threat,
            associated_assets=associated_assets,
            threat_asset_association_id=threat_asset_association_id,
            pirs=pirs,
            threat_feed_name=threat_feed_name,
        )

        # 6. 儲存風險評估
        await self.risk_assessment_repository.save(risk_assessment)

        # 7. 儲存歷史記錄（AC-012-5）
        await self.history_repository.save_history(risk_assessment)

        # 8. 發布風險評估完成事件
        event = RiskAssessmentCompletedEvent(
            risk_assessment_id=risk_assessment.id,
            threat_id=threat_id,
            final_risk_score=risk_assessment.final_risk_score,
            risk_level=risk_assessment.risk_level,
            affected_asset_count=risk_assessment.affected_asset_count,
            completed_at=risk_assessment.updated_at or risk_assessment.created_at,
        )
        
        event_bus = get_event_bus()
        await event_bus.publish(event)

        logger.info(
            "風險評估計算完成並已儲存歷史記錄",
            threat_id=threat_id,
            risk_assessment_id=risk_assessment.id,
            final_risk_score=risk_assessment.final_risk_score,
        )

        return risk_assessment

    async def get_risk_assessment_by_threat_id(
        self,
        threat_id: str,
    ) -> Optional[RiskAssessment]:
        """
        查詢威脅的風險評估
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            Optional[RiskAssessment]: 風險評估聚合根，如果不存在則返回 None
        """
        return await self.risk_assessment_repository.get_by_threat_id(threat_id)

    async def get_risk_assessment_history(
        self,
        risk_assessment_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[dict]:
        """
        查詢風險評估歷史記錄（AC-013-3）
        
        Args:
            risk_assessment_id: 風險評估 ID
            start_time: 開始時間（可選）
            end_time: 結束時間（可選）
        
        Returns:
            List[dict]: 歷史記錄清單
        """
        if start_time or end_time:
            return await self.history_repository.get_by_time_range(
                risk_assessment_id, start_time, end_time
            )
        else:
            return await self.history_repository.get_by_risk_assessment_id(
                risk_assessment_id
            )

    async def get_latest_risk_assessment(
        self,
        risk_assessment_id: str,
    ) -> Optional[dict]:
        """
        查詢最新的風險評估記錄
        
        Args:
            risk_assessment_id: 風險評估 ID
        
        Returns:
            Optional[dict]: 最新的歷史記錄，如果沒有則返回 None
        """
        return await self.history_repository.get_latest(risk_assessment_id)

    async def _get_associated_assets(self, threat_id: str) -> List[Asset]:
        """
        取得受影響的資產清單
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            List[Asset]: 受影響的資產清單
        """
        # 從 threat_asset_association 查詢關聯的資產
        associations = await self.association_repository.get_by_threat_id(threat_id)
        
        # 取得所有關聯的資產
        assets = []
        for association in associations:
            asset = await self.asset_repository.get_by_id(association.asset_id)
            if asset:
                assets.append(asset)
        
        return assets

