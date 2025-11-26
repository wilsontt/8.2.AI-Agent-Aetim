"""
風險評估完成事件

當風險評估完成時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RiskAssessmentCompletedEvent:
    """風險評估完成事件"""
    
    risk_assessment_id: str
    threat_id: str
    final_risk_score: float
    risk_level: str
    affected_asset_count: int
    completed_at: datetime
    
    def __str__(self) -> str:
        return (
            f"RiskAssessmentCompletedEvent(risk_assessment_id='{self.risk_assessment_id}', "
            f"threat_id='{self.threat_id}', "
            f"final_risk_score={self.final_risk_score}, "
            f"risk_level='{self.risk_level}', "
            f"completed_at='{self.completed_at.isoformat()}')"
        )

