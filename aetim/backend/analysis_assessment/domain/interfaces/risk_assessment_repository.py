"""
風險評估 Repository 介面

定義風險評估的資料存取介面。
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

from ..aggregates.risk_assessment import RiskAssessment


class IRiskAssessmentRepository(ABC):
    """
    風險評估 Repository 介面
    
    定義風險評估的資料存取方法。
    """

    @abstractmethod
    async def save(self, risk_assessment: RiskAssessment) -> None:
        """
        儲存風險評估（新增或更新）
        
        Args:
            risk_assessment: 風險評估聚合根
        """
        pass

    @abstractmethod
    async def get_by_id(self, risk_assessment_id: str) -> Optional[RiskAssessment]:
        """
        依 ID 查詢風險評估
        
        Args:
            risk_assessment_id: 風險評估 ID
        
        Returns:
            Optional[RiskAssessment]: 風險評估聚合根，如果不存在則返回 None
        """
        pass

    @abstractmethod
    async def get_by_threat_id(self, threat_id: str) -> Optional[RiskAssessment]:
        """
        依威脅 ID 查詢風險評估
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            Optional[RiskAssessment]: 風險評估聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_by_risk_score_range(
        self,
        min_risk_score: float,
        max_risk_score: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[RiskAssessment]:
        """
        依風險分數範圍查詢風險評估
        
        Args:
            min_risk_score: 最小風險分數
            max_risk_score: 最大風險分數（可選，如果不提供則不設上限）
            start_date: 開始日期（可選）
            end_date: 結束日期（可選）
        
        Returns:
            List[RiskAssessment]: 風險評估聚合根清單
        """
        pass

