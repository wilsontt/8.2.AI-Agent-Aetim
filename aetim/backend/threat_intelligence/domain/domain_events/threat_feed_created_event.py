"""
威脅情資來源建立領域事件

當威脅情資來源被建立時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ThreatFeedCreatedEvent:
    """
    威脅情資來源建立領域事件
    
    當威脅情資來源被建立時，系統會發布此事件。
    其他模組可以訂閱此事件以執行相關操作（例如：初始化收集排程）。
    """
    
    threat_feed_id: str
    name: str
    priority: str
    collection_frequency: str
    occurred_at: datetime = None
    
    def __post_init__(self):
        """設定事件發生時間"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.utcnow())
    
    def __repr__(self):
        return (
            f"ThreatFeedCreatedEvent(threat_feed_id='{self.threat_feed_id}', "
            f"name='{self.name}', "
            f"priority='{self.priority}', "
            f"occurred_at={self.occurred_at})"
        )

