"""
加權因子計算服務

實作加權因子計算邏輯，符合 AC-012-2 的要求。
"""

from typing import List, Optional

from threat_intelligence.domain.aggregates.threat import Threat
from asset_management.domain.aggregates.asset import Asset
from analysis_assessment.domain.aggregates.pir import PIR
import structlog

logger = structlog.get_logger(__name__)


class WeightFactorCalculator:
    """
    加權因子計算服務（Domain Service）
    
    負責計算各種加權因子：
    1. 資產重要性加權
    2. 受影響資產數量加權
    3. PIR 符合度加權
    4. CISA KEV 加權
    """
    
    # 權重常數
    ASSET_COUNT_WEIGHT_PER_10 = 0.1  # 每增加 10 個資產，風險分數增加 0.1
    PIR_HIGH_PRIORITY_WEIGHT = 0.3  # 符合高優先級 PIR，風險分數增加 0.3
    CISA_KEV_WEIGHT = 0.5  # 在 CISA KEV 清單中，風險分數增加 0.5
    
    def calculate_asset_importance_weight(
        self,
        associated_assets: List[Asset],
    ) -> float:
        """
        計算資產重要性加權（AC-012-2）
        
        計算公式：weight = data_sensitivity.weight * business_criticality.weight
        權重值：高=1.5、中=1.0、低=0.5
        
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
    
    def calculate_asset_count_weight(self, affected_asset_count: int) -> float:
        """
        計算受影響資產數量加權（AC-012-2）
        
        計算公式：weight = (affected_count / 10.0) * 0.1
        每增加 10 個資產，風險分數增加 0.1
        
        Args:
            affected_asset_count: 受影響資產數量
        
        Returns:
            float: 資產數量加權
        """
        if affected_asset_count <= 0:
            return 0.0
        
        asset_count_weight = (
            affected_asset_count / 10.0
        ) * self.ASSET_COUNT_WEIGHT_PER_10
        
        logger.debug(
            "計算資產數量加權",
            affected_asset_count=affected_asset_count,
            asset_count_weight=asset_count_weight,
        )
        
        return asset_count_weight
    
    def calculate_pir_match_weight(
        self,
        threat: Threat,
        pirs: List[PIR],
    ) -> float:
        """
        計算 PIR 符合度加權（AC-012-2）
        
        檢查威脅是否符合 PIR 條件：
        - 產品名稱匹配
        - CVE 編號匹配
        - 威脅類型匹配
        
        符合高優先級 PIR，返回 0.3
        否則返回 0.0
        
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
    
    def calculate_cisa_kev_weight(
        self,
        threat: Threat,
        threat_feed_name: Optional[str] = None,
    ) -> float:
        """
        計算 CISA KEV 加權（AC-012-2）
        
        檢查是否在 CISA KEV 清單中。
        如果在 CISA KEV 清單中，返回 0.5
        否則返回 0.0
        
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

