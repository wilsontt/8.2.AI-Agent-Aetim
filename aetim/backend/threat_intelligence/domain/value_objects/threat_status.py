"""
威脅狀態值物件

定義威脅的生命週期狀態。
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ThreatStatus:
    """
    威脅狀態值物件
    
    值物件是不可變的，確保狀態的一致性。
    
    狀態定義（AC-014-3）：
    - New: 新增（剛收集到的威脅）
    - Analyzing: 分析中（正在進行關聯分析）
    - Processed: 已處理（已完成分析與風險評估）
    - Closed: 已關閉（威脅已處理或不再相關）
    """
    
    value: str  # New, Analyzing, Processed, Closed
    
    # 有效值列表
    VALID_VALUES = ["New", "Analyzing", "Processed", "Closed"]
    
    def __post_init__(self):
        """驗證狀態值"""
        if self.value not in self.VALID_VALUES:
            raise ValueError(
                f"狀態必須為 {', '.join(self.VALID_VALUES)} 之一，"
                f"但收到：{self.value}"
            )
    
    def can_transition_to(self, target_status: str) -> bool:
        """
        檢查是否可以轉換到目標狀態
        
        Args:
            target_status: 目標狀態
        
        Returns:
            bool: 是否可以轉換
        """
        if target_status not in self.VALID_VALUES:
            return False
        
        allowed_transitions = ThreatStatus.TRANSITION_RULES.get(self.value, [])
        return target_status in allowed_transitions
    
    def __str__(self) -> str:
        return self.value


# 狀態轉換規則（從當前狀態可以轉換到哪些狀態）（類別變數，在類別定義後設定以避免 dataclass 欄位問題）
ThreatStatus.TRANSITION_RULES: Dict[str, List[str]] = {
    "New": ["Analyzing", "Closed"],
    "Analyzing": ["Processed", "Closed"],
    "Processed": ["Closed"],
    "Closed": [],  # 已關閉的狀態不能再轉換
}
