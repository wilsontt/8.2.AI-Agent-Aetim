"""
資產更新領域事件

當資產被更新時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AssetUpdatedEvent:
    """
    資產更新領域事件
    
    當資產被更新時，系統會發布此事件。
    其他模組可以訂閱此事件以執行相關操作（例如：重新計算風險分數）。
    """
    
    asset_id: str
    host_name: str
    updated_fields: list[str]  # 被更新的欄位清單
    occurred_at: datetime = None
    
    def __post_init__(self):
        """設定事件發生時間"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.utcnow())
    
    def __repr__(self):
        return (
            f"AssetUpdatedEvent(asset_id='{self.asset_id}', "
            f"host_name='{self.host_name}', "
            f"updated_fields={self.updated_fields}, "
            f"occurred_at={self.occurred_at})"
        )

