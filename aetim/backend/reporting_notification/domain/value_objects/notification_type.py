"""
通知類型值物件

定義通知類型的枚舉值。
"""

from enum import Enum


class NotificationType(str, Enum):
    """通知類型枚舉（AC-021-1）"""
    
    CRITICAL = "Critical"  # 嚴重威脅通知
    HIGH_RISK_DAILY = "HighRiskDaily"  # 高風險每日摘要
    WEEKLY = "Weekly"  # 週報通知
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def from_string(cls, value: str) -> "NotificationType":
        """從字串建立通知類型"""
        mapping = {
            "Critical": cls.CRITICAL,
            "HighRiskDaily": cls.HIGH_RISK_DAILY,
            "Weekly": cls.WEEKLY,
            "critical": cls.CRITICAL,
            "highriskdaily": cls.HIGH_RISK_DAILY,
            "weekly": cls.WEEKLY,
        }
        
        if value in mapping:
            return mapping[value]
        
        raise ValueError(f"無效的通知類型: {value}")
    
    def get_default_risk_threshold(self) -> float | None:
        """
        取得預設風險分數閾值（AC-021-1）
        
        Returns:
            float | None: 風險分數閾值，週報通知返回 None
        """
        thresholds = {
            NotificationType.CRITICAL: 8.0,  # 嚴重威脅通知：風險分數 ≥ 8.0
            NotificationType.HIGH_RISK_DAILY: 6.0,  # 高風險每日摘要：風險分數 ≥ 6.0
            NotificationType.WEEKLY: None,  # 週報通知：由排程觸發
        }
        return thresholds.get(self)

