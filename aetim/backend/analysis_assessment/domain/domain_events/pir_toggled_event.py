"""
PIR 啟用/停用領域事件

當 PIR 的啟用狀態被變更時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PIRToggledEvent:
    """
    PIR 啟用/停用領域事件
    
    當 PIR 的啟用狀態被變更時，系統會發布此事件。
    其他模組可以訂閱此事件以執行相關操作（例如：更新威脅分析規則）。
    """
    
    pir_id: str
    name: str
    is_enabled: bool
    occurred_at: datetime = None
    
    def __post_init__(self):
        """設定事件發生時間"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.utcnow())
    
    def __repr__(self):
        return (
            f"PIRToggledEvent(pir_id='{self.pir_id}', "
            f"name='{self.name}', "
            f"is_enabled={self.is_enabled}, "
            f"occurred_at={self.occurred_at})"
        )

