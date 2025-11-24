"""
風險計算服務

實作風險分數計算邏輯，符合 AC-012-1 至 AC-012-5 的要求。
"""

from typing import List, Optional, Dict, Any

from threat_intelligence.domain.aggregates.threat import Threat
from asset_management.domain.aggregates.asset import Asset
from analysis_assessment.domain.aggregates.pir import PIR
from analysis_assessment.domain.aggregates.risk_assessment import RiskAssessment
from analysis_assessment.domain.domain_services.cvss_score_calculator import (
    CVSSScoreCalculator,
)
from analysis_assessment.domain.domain_services.weight_factor_calculator import (
    WeightFactorCalculator,
)
from analysis_assessment.domain.domain_services.risk_level_classifier import (
    RiskLevelClassifier,
)
import structlog

logger = structlog.get_logger(__name__)


class RiskCalculationService:
    """
    風險計算服務（Domain Service）
    
    負責計算威脅的風險分數，考慮以下因素：
    1. 基礎 CVSS 分數（AC-012-1）
    2. 資產重要性加權（AC-012-2）
    3. 受影響資產數量加權（AC-012-2）
    4. PIR 符合度加權（AC-012-2）
    5. CISA KEV 加權（AC-012-2）
    
    計算公式（AC-012-3）：
    final_score = base_score * asset_weight + asset_count_weight + pir_weight + cisa_kev_weight
    """
    
    def __init__(
        self,
        cvss_calculator: Optional[CVSSScoreCalculator] = None,
        weight_calculator: Optional[WeightFactorCalculator] = None,
        risk_classifier: Optional[RiskLevelClassifier] = None,
    ):
        """
        初始化風險計算服務
        
        Args:
            cvss_calculator: CVSS 分數計算器（可選，預設建立新實例）
            weight_calculator: 加權因子計算器（可選，預設建立新實例）
            risk_classifier: 風險等級分類器（可選，預設建立新實例）
        """
        self.cvss_calculator = cvss_calculator or CVSSScoreCalculator()
        self.weight_calculator = weight_calculator or WeightFactorCalculator()
        self.risk_classifier = risk_classifier or RiskLevelClassifier()
    
    def calculate_risk(
        self,
        threat: Threat,
        associated_assets: List[Asset],
        threat_asset_association_id: str,
        pirs: List[PIR],
        threat_feed_name: Optional[str] = None,
    ) -> RiskAssessment:
        """
        計算風險評估（AC-012-1 至 AC-012-5）
        
        Args:
            threat: 威脅聚合根
            associated_assets: 受影響的資產清單
            threat_asset_association_id: 威脅資產關聯 ID
            pirs: PIR 清單（用於檢查符合度）
            threat_feed_name: 威脅來源名稱（用於判斷是否為 CISA KEV）
        
        Returns:
            RiskAssessment: 風險評估聚合根
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        logger.info(
            "開始計算風險評估",
            threat_id=threat.id,
            asset_count=len(associated_assets),
        )
        
        # 1. 計算基礎 CVSS 分數（AC-012-1）
        base_cvss_score = self.cvss_calculator.calculate_base_score(threat)
        
        # 2. 計算資產重要性加權（AC-012-2）
        asset_importance_weight = self.weight_calculator.calculate_asset_importance_weight(
            associated_assets
        )
        
        # 3. 計算受影響資產數量加權（AC-012-2）
        affected_asset_count = len(associated_assets)
        asset_count_weight = self.weight_calculator.calculate_asset_count_weight(
            affected_asset_count
        )
        
        # 4. 計算 PIR 符合度加權（AC-012-2）
        pir_match_weight = self.weight_calculator.calculate_pir_match_weight(threat, pirs)
        
        # 5. 計算 CISA KEV 加權（AC-012-2）
        cisa_kev_weight = self.weight_calculator.calculate_cisa_kev_weight(
            threat, threat_feed_name
        )
        
        # 6. 計算最終風險分數（AC-012-3）
        final_risk_score = (
            base_cvss_score * asset_importance_weight
            + asset_count_weight
            + pir_match_weight
            + cisa_kev_weight
        )
        
        # 確保最終風險分數在 0.0 - 10.0 範圍內
        final_risk_score = max(0.0, min(10.0, final_risk_score))
        
        # 7. 決定風險等級（AC-012-4）
        risk_level = self.risk_classifier.classify(final_risk_score)
        
        # 8. 記錄計算過程（AC-012-5）
        calculation_details = {
            "base_cvss_score": base_cvss_score,
            "asset_importance_weight": asset_importance_weight,
            "affected_asset_count": affected_asset_count,
            "asset_count_weight": asset_count_weight,
            "pir_match_weight": pir_match_weight,
            "cisa_kev_weight": cisa_kev_weight,
            "calculation_formula": (
                f"final_score = {base_cvss_score} * {asset_importance_weight} + "
                f"{asset_count_weight} + {pir_match_weight} + {cisa_kev_weight}"
            ),
            "final_risk_score": final_risk_score,
            "risk_level": risk_level,
        }
        
        logger.info(
            "風險評估計算完成",
            threat_id=threat.id,
            final_risk_score=final_risk_score,
            risk_level=risk_level,
        )
        
        # 建立風險評估聚合根
        risk_assessment = RiskAssessment.create(
            threat_id=threat.id,
            threat_asset_association_id=threat_asset_association_id,
            base_cvss_score=base_cvss_score,
            asset_importance_weight=asset_importance_weight,
            affected_asset_count=affected_asset_count,
            asset_count_weight=asset_count_weight,
            pir_match_weight=pir_match_weight,
            cisa_kev_weight=cisa_kev_weight,
            final_risk_score=final_risk_score,
            risk_level=risk_level,
            calculation_details=calculation_details,
        )
        
        return risk_assessment

