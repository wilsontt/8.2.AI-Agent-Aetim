"""
風險評估聚合根

風險評估聚合根包含所有業務邏輯方法，負責維護風險評估的一致性。
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json


@dataclass
class RiskAssessment:
    """
    風險評估聚合根
    
    聚合根負責：
    1. 維護聚合的一致性邊界
    2. 實作業務邏輯
    3. 記錄風險分數的計算過程（AC-012-5）
    
    業務規則：
    - 最終風險分數必須在 0.0 - 10.0 範圍內（AC-012-3）
    - 風險等級必須根據最終風險分數決定（AC-012-4）
    """
    
    id: str
    threat_id: str
    threat_asset_association_id: str
    
    # 風險分數計算
    base_cvss_score: float
    asset_importance_weight: float
    affected_asset_count: int
    asset_count_weight: float
    
    # 最終結果
    final_risk_score: float
    risk_level: str  # Critical, High, Medium, Low
    
    # 可選加權
    pir_match_weight: Optional[float] = None
    cisa_kev_weight: Optional[float] = None
    
    # 計算詳情
    calculation_details: Optional[Dict[str, Any]] = None
    
    # 時間戳記
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """驗證聚合根的有效性"""
        if not self.threat_id:
            raise ValueError("威脅 ID 不能為空")
        
        if not self.threat_asset_association_id:
            raise ValueError("威脅資產關聯 ID 不能為空")
        
        if self.base_cvss_score < 0.0 or self.base_cvss_score > 10.0:
            raise ValueError("基礎 CVSS 分數必須在 0.0 - 10.0 範圍內")
        
        if self.final_risk_score < 0.0 or self.final_risk_score > 10.0:
            raise ValueError("最終風險分數必須在 0.0 - 10.0 範圍內")
        
        if self.risk_level not in ["Critical", "High", "Medium", "Low"]:
            raise ValueError("風險等級必須為 Critical、High、Medium 或 Low")
    
    @classmethod
    def create(
        cls,
        threat_id: str,
        threat_asset_association_id: str,
        base_cvss_score: float,
        asset_importance_weight: float,
        affected_asset_count: int,
        asset_count_weight: float,
        final_risk_score: float,
        risk_level: str,
        pir_match_weight: Optional[float] = None,
        cisa_kev_weight: Optional[float] = None,
        calculation_details: Optional[Dict[str, Any]] = None,
    ) -> "RiskAssessment":
        """
        建立風險評估（工廠方法）
        
        Args:
            threat_id: 威脅 ID
            threat_asset_association_id: 威脅資產關聯 ID
            base_cvss_score: 基礎 CVSS 分數
            asset_importance_weight: 資產重要性加權
            affected_asset_count: 受影響資產數量
            asset_count_weight: 資產數量加權
            final_risk_score: 最終風險分數
            risk_level: 風險等級
            pir_match_weight: PIR 符合度加權（可選）
            cisa_kev_weight: CISA KEV 加權（可選）
            calculation_details: 計算詳情（可選）
        
        Returns:
            RiskAssessment: 新建立的風險評估聚合根
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        # 確保最終風險分數在範圍內
        final_risk_score = max(0.0, min(10.0, final_risk_score))
        
        risk_assessment = cls(
            id=str(uuid.uuid4()),
            threat_id=threat_id,
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
    
    def update_calculation(
        self,
        base_cvss_score: Optional[float] = None,
        asset_importance_weight: Optional[float] = None,
        affected_asset_count: Optional[int] = None,
        asset_count_weight: Optional[float] = None,
        pir_match_weight: Optional[float] = None,
        cisa_kev_weight: Optional[float] = None,
        final_risk_score: Optional[float] = None,
        risk_level: Optional[str] = None,
        calculation_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        更新風險評估計算結果
        
        Args:
            base_cvss_score: 基礎 CVSS 分數（可選）
            asset_importance_weight: 資產重要性加權（可選）
            affected_asset_count: 受影響資產數量（可選）
            asset_count_weight: 資產數量加權（可選）
            pir_match_weight: PIR 符合度加權（可選）
            cisa_kev_weight: CISA KEV 加權（可選）
            final_risk_score: 最終風險分數（可選）
            risk_level: 風險等級（可選）
            calculation_details: 計算詳情（可選）
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        if base_cvss_score is not None:
            if base_cvss_score < 0.0 or base_cvss_score > 10.0:
                raise ValueError("基礎 CVSS 分數必須在 0.0 - 10.0 範圍內")
            self.base_cvss_score = base_cvss_score
        
        if asset_importance_weight is not None:
            self.asset_importance_weight = asset_importance_weight
        
        if affected_asset_count is not None:
            self.affected_asset_count = affected_asset_count
        
        if asset_count_weight is not None:
            self.asset_count_weight = asset_count_weight
        
        if pir_match_weight is not None:
            self.pir_match_weight = pir_match_weight
        
        if cisa_kev_weight is not None:
            self.cisa_kev_weight = cisa_kev_weight
        
        if final_risk_score is not None:
            # 確保最終風險分數在範圍內
            final_risk_score = max(0.0, min(10.0, final_risk_score))
            self.final_risk_score = final_risk_score
        
        if risk_level is not None:
            if risk_level not in ["Critical", "High", "Medium", "Low"]:
                raise ValueError("風險等級必須為 Critical、High、Medium 或 Low")
            self.risk_level = risk_level
        
        if calculation_details is not None:
            self.calculation_details = calculation_details
        
        self.updated_at = datetime.utcnow()
    
    def get_calculation_details_json(self) -> Optional[str]:
        """
        取得計算詳情的 JSON 字串
        
        Returns:
            Optional[str]: 計算詳情的 JSON 字串，如果沒有則返回 None
        """
        if self.calculation_details is None:
            return None
        return json.dumps(self.calculation_details, ensure_ascii=False, indent=2)
    
    @staticmethod
    def determine_risk_level(final_risk_score: float) -> str:
        """
        根據最終風險分數決定風險等級（AC-012-4）
        
        此方法與 RiskLevelClassifier 保持一致。
        
        Args:
            final_risk_score: 最終風險分數
        
        Returns:
            str: 風險等級（Critical, High, Medium, Low）
        """
        from ..domain_services.risk_level_classifier import RiskLevelClassifier
        
        classifier = RiskLevelClassifier()
        return classifier.classify(final_risk_score)
    
    def __repr__(self):
        return (
            f"RiskAssessment(id='{self.id}', "
            f"threat_id='{self.threat_id}', "
            f"final_risk_score={self.final_risk_score}, "
            f"risk_level='{self.risk_level}')"
        )

