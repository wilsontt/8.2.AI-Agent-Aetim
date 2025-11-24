"""
風險評估歷史記錄 Repository 介面

定義風險評估歷史記錄的資料存取介面。
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..aggregates.risk_assessment import RiskAssessment


class IRiskAssessmentHistoryRepository(ABC):
    """
    風險評估歷史記錄 Repository 介面
    
    定義風險評估歷史記錄的資料存取方法。
    """

    @abstractmethod
    async def save_history(
        self,
        risk_assessment: RiskAssessment,
    ) -> None:
        """
        儲存風險評估歷史記錄（AC-012-5）
        
        Args:
            risk_assessment: 風險評估聚合根
        """
        pass

    @abstractmethod
    async def get_by_risk_assessment_id(
        self,
        risk_assessment_id: str,
    ) -> List[dict]:
        """
        查詢風險評估的歷史記錄（AC-013-3）
        
        Args:
            risk_assessment_id: 風險評估 ID
        
        Returns:
            List[dict]: 歷史記錄清單
        """
        pass

    @abstractmethod
    async def get_latest(
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
        pass

    @abstractmethod
    async def get_by_time_range(
        self,
        risk_assessment_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[dict]:
        """
        根據時間範圍查詢歷史記錄
        
        Args:
            risk_assessment_id: 風險評估 ID
            start_time: 開始時間（可選）
            end_time: 結束時間（可選）
        
        Returns:
            List[dict]: 歷史記錄清單
        """
        pass

