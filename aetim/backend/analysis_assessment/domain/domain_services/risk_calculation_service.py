"""
風險計算服務

實作風險分數計算邏輯，符合 AC-012-1 至 AC-012-5 的要求。
"""

from typing import List, Optional, Dict, Any

from threat_intelligence.domain.aggregates.threat import Threat
from asset_management.domain.aggregates.asset import Asset
from analysis_assessment.domain.aggregates.pir import PIR
from analysis_assessment.domain.aggregates.risk_assessment import RiskAssessment
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
    
    # 權重常數
    ASSET_COUNT_WEIGHT_PER_10 = 0.1  # 每增加 10 個資產，風險分數增加 0.1
    PIR_HIGH_PRIORITY_WEIGHT = 0.3  # 符合高優先級 PIR，風險分數增加 0.3
    CISA_KEV_WEIGHT = 0.5  # 在 CISA KEV 清單中，風險分數增加 0.5
    
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
        base_cvss_score = self._calculate_base_cvss_score(threat)
        
        # 2. 計算資產重要性加權（AC-012-2）
        asset_importance_weight = self._calculate_asset_importance_weight(associated_assets)
        
        # 3. 計算受影響資產數量加權（AC-012-2）
        affected_asset_count = len(associated_assets)
        asset_count_weight = self._calculate_asset_count_weight(affected_asset_count)
        
        # 4. 計算 PIR 符合度加權（AC-012-2）
        pir_match_weight = self._check_pir_match(threat, pirs)
        
        # 5. 計算 CISA KEV 加權（AC-012-2）
        cisa_kev_weight = self._check_cisa_kev(threat, threat_feed_name)
        
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
        risk_level = RiskAssessment.determine_risk_level(final_risk_score)
        
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
    
    def _calculate_base_cvss_score(self, threat: Threat) -> float:
        """
        計算基礎 CVSS 分數（AC-012-1）
        
        Args:
            threat: 威脅聚合根
        
        Returns:
            float: 基礎 CVSS 分數（0.0 - 10.0）
        """
        if threat.cvss_base_score is not None:
            return float(threat.cvss_base_score)
        
        # 如果沒有 CVSS 分數，預設為 0.0
        logger.warning(
            "威脅沒有 CVSS 分數，使用預設值 0.0",
            threat_id=threat.id,
        )
        return 0.0
    
    def _calculate_asset_importance_weight(
        self,
        associated_assets: List[Asset],
    ) -> float:
        """
        計算資產重要性加權（AC-012-2）
        
        計算公式：asset_weight = data_sensitivity.weight * business_criticality.weight
        
        如果有多個資產，使用平均權重。
        
        Args:
            associated_assets: 受影響的資產清單
        
        Returns:
            float: 資產重要性加權
        """
        if not associated_assets:
            return 1.0  # 預設權重
        
        total_weight = 0.0
        for asset in associated_assets:
            # 計算單一資產的權重
            asset_weight = (
                asset.data_sensitivity.weight * asset.business_criticality.weight
            )
            total_weight += asset_weight
        
        # 計算平均權重
        average_weight = total_weight / len(associated_assets)
        
        logger.debug(
            "計算資產重要性加權",
            asset_count=len(associated_assets),
            average_weight=average_weight,
        )
        
        return average_weight
    
    def _calculate_asset_count_weight(self, affected_asset_count: int) -> float:
        """
        計算受影響資產數量加權（AC-012-2）
        
        計算公式：asset_count_weight = (affected_count / 10.0) * 0.1
        每增加 10 個資產，風險分數增加 0.1
        
        Args:
            affected_asset_count: 受影響資產數量
        
        Returns:
            float: 資產數量加權
        """
        if affected_asset_count <= 0:
            return 0.0
        
        asset_count_weight = (affected_asset_count / 10.0) * self.ASSET_COUNT_WEIGHT_PER_10
        
        logger.debug(
            "計算資產數量加權",
            affected_asset_count=affected_asset_count,
            asset_count_weight=asset_count_weight,
        )
        
        return asset_count_weight
    
    def _check_pir_match(self, threat: Threat, pirs: List[PIR]) -> float:
        """
        檢查 PIR 符合度並計算加權（AC-012-2）
        
        符合高優先級 PIR，風險分數增加 0.3
        只檢查啟用的 PIR
        
        Args:
            threat: 威脅聚合根
            pirs: PIR 清單
        
        Returns:
            float: PIR 符合度加權（符合高優先級 PIR：0.3，否則：0.0）
        """
        if not pirs:
            return 0.0
        
        # 準備威脅資料用於 PIR 匹配
        threat_data = {
            "cve": threat.cve_id or "",
            "product_name": ", ".join([p.product_name for p in threat.products]),
            "threat_type": threat.title,
            "cvss_score": threat.cvss_base_score or 0.0,
        }
        
        # 檢查是否有高優先級 PIR 符合
        for pir in pirs:
            # 只檢查啟用的 PIR
            if not pir.is_enabled:
                continue
            
            # 檢查是否為高優先級
            if pir.priority.value != "高":
                continue
            
            # 檢查是否符合條件
            if pir.matches_condition(threat_data):
                logger.info(
                    "威脅符合高優先級 PIR",
                    threat_id=threat.id,
                    pir_id=pir.id,
                    pir_name=pir.name,
                )
                return self.PIR_HIGH_PRIORITY_WEIGHT
        
        return 0.0
    
    def _check_cisa_kev(
        self,
        threat: Threat,
        threat_feed_name: Optional[str] = None,
    ) -> float:
        """
        檢查是否在 CISA KEV 清單中並計算加權（AC-012-2）
        
        是否在 CISA KEV 清單中，是則風險分數增加 0.5
        
        Args:
            threat: 威脅聚合根
            threat_feed_name: 威脅來源名稱（用於判斷是否為 CISA KEV）
        
        Returns:
            float: CISA KEV 加權（在清單中：0.5，否則：0.0）
        """
        if threat_feed_name:
            # 檢查威脅來源名稱是否包含 "CISA" 或 "KEV"
            threat_feed_name_lower = threat_feed_name.lower()
            if "cisa" in threat_feed_name_lower or "kev" in threat_feed_name_lower:
                logger.info(
                    "威脅在 CISA KEV 清單中",
                    threat_id=threat.id,
                    threat_feed_name=threat_feed_name,
                )
                return self.CISA_KEV_WEIGHT
        
        return 0.0

