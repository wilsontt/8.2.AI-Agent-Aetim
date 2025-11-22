"""
威脅情資來源更新領域事件

當威脅情資來源被更新時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ThreatFeedUpdatedEvent:
    """
    威脅情資來源更新領域事件
    
    當威脅情資來源被更新時，系統會發布此事件。
    其他模組可以訂閱此事件以執行相關操作（例如：更新收集排程）。
    """
    
    threat_feed_id: str
    name: str
    updated_fields: list[str]  # 被更新的欄位清單
    occurred_at: datetime = None
    
    def __post_init__(self):
        """設定事件發生時間"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.utcnow())
    
    def __repr__(self):
        return (
            f"ThreatFeedUpdatedEvent(threat_feed_id='{self.threat_feed_id}', "
            f"name='{self.name}', "
            f"updated_fields={self.updated_fields}, "
            f"occurred_at={self.occurred_at})"
        )

