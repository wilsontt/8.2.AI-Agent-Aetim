"""
風險分數分類服務

實作風險分數分類邏輯，符合 AC-012-4 的要求。
"""

from typing import Literal

import structlog

logger = structlog.get_logger(__name__)

# 風險等級類型
RiskLevel = Literal["Critical", "High", "Medium", "Low"]


class RiskLevelClassifier:
    """
    風險分數分類服務（Domain Service）
    
    負責根據風險分數將威脅分類為不同的風險等級。
    
    分類規則（AC-012-4）：
    - 嚴重（Critical）：≥ 8.0
    - 高（High）：6.0 - 7.9
    - 中（Medium）：4.0 - 5.9
    - 低（Low）：< 4.0
    """
    
    # 風險等級閾值
    CRITICAL_THRESHOLD = 8.0
    HIGH_THRESHOLD = 6.0
    MEDIUM_THRESHOLD = 4.0
    
    def classify(self, risk_score: float) -> RiskLevel:
        """
        分類風險等級（AC-012-4）
        
        Args:
            risk_score: 風險分數（0.0 - 10.0）
        
        Returns:
            RiskLevel: 風險等級（Critical, High, Medium, Low）
        
        Raises:
            ValueError: 當風險分數不在有效範圍內時
        """
        if risk_score < 0.0 or risk_score > 10.0:
            raise ValueError(
                f"風險分數必須在 0.0 - 10.0 範圍內，收到：{risk_score}"
            )
        
        if risk_score >= self.CRITICAL_THRESHOLD:
            return "Critical"
        elif risk_score >= self.HIGH_THRESHOLD:
            return "High"
        elif risk_score >= self.MEDIUM_THRESHOLD:
            return "Medium"
        else:
            return "Low"
    
    def get_risk_level_label(self, risk_level: RiskLevel) -> str:
        """
        取得風險等級的中文標籤
        
        Args:
            risk_level: 風險等級
        
        Returns:
            str: 風險等級的中文標籤
        """
        labels = {
            "Critical": "嚴重",
            "High": "高",
            "Medium": "中",
            "Low": "低",
        }
        return labels.get(risk_level, risk_level)
    
    def get_risk_level_color(self, risk_level: RiskLevel) -> str:
        """
        取得風險等級的顏色（用於 UI 顯示）
        
        Args:
            risk_level: 風險等級
        
        Returns:
            str: 風險等級的顏色（CSS 類別名稱）
        """
        colors = {
            "Critical": "bg-red-100 text-red-800",
            "High": "bg-orange-100 text-orange-800",
            "Medium": "bg-yellow-100 text-yellow-800",
            "Low": "bg-green-100 text-green-800",
        }
        return colors.get(risk_level, "bg-gray-100 text-gray-800")
    
    @staticmethod
    def determine_risk_level(risk_score: float) -> RiskLevel:
        """
        決定風險等級（靜態方法，與 RiskAssessment 聚合根保持一致）
        
        Args:
            risk_score: 風險分數（0.0 - 10.0）
        
        Returns:
            RiskLevel: 風險等級（Critical, High, Medium, Low）
        """
        classifier = RiskLevelClassifier()
        return classifier.classify(risk_score)

