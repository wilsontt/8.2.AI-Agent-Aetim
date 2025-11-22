"""
收集狀態更新領域事件

當威脅情資來源的收集狀態被更新時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CollectionStatusUpdatedEvent:
    """
    收集狀態更新領域事件
    
    當威脅情資來源的收集狀態被更新時，系統會發布此事件。
    其他模組可以訂閱此事件以執行相關操作（例如：觸發通知）。
    """
    
    threat_feed_id: str
    name: str
    status: str
    record_count: int = 0
    error_message: str = None
    occurred_at: datetime = None
    
    def __post_init__(self):
        """設定事件發生時間"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.utcnow())
    
    def __repr__(self):
        return (
            f"CollectionStatusUpdatedEvent(threat_feed_id='{self.threat_feed_id}', "
            f"name='{self.name}', "
            f"status='{self.status}', "
            f"record_count={self.record_count}, "
            f"occurred_at={self.occurred_at})"
        )

