"""
資產建立領域事件

當資產被建立時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AssetCreatedEvent:
    """
    資產建立領域事件
    
    當資產被建立時，系統會發布此事件。
    其他模組可以訂閱此事件以執行相關操作（例如：觸發威脅關聯分析）。
    """
    
    asset_id: str
    host_name: str
    owner: str
    occurred_at: datetime = None
    
    def __post_init__(self):
        """設定事件發生時間"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.utcnow())
    
    def __repr__(self):
        return (
            f"AssetCreatedEvent(asset_id='{self.asset_id}', "
            f"host_name='{self.host_name}', "
            f"occurred_at={self.occurred_at})"
        )

