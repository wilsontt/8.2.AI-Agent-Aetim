"""
威脅嚴重程度值物件

定義威脅的嚴重程度等級。
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ThreatSeverity:
    """
    威脅嚴重程度值物件
    
    值物件是不可變的，確保嚴重程度的一致性。
    """
    
    value: str  # Critical, High, Medium, Low
    
    # 嚴重程度權重（用於風險計算）
    WEIGHTS: Dict[str, float] = {
        "Critical": 1.5,
        "High": 1.2,
        "Medium": 1.0,
        "Low": 0.8,
    }
    
    # 有效值列表
    VALID_VALUES = ["Critical", "High", "Medium", "Low"]
    
    def __post_init__(self):
        """驗證嚴重程度值"""
        if self.value not in self.VALID_VALUES:
            raise ValueError(
                f"嚴重程度必須為 {', '.join(self.VALID_VALUES)} 之一，"
                f"但收到：{self.value}"
            )
    
    @property
    def weight(self) -> float:
        """取得嚴重程度權重"""
        return self.WEIGHTS.get(self.value, 1.0)
    
    def __str__(self) -> str:
        return self.value

