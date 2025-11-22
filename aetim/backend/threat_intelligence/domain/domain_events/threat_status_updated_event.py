"""
威脅狀態更新事件

當威脅狀態被更新時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ThreatStatusUpdatedEvent:
    """
    威脅狀態更新事件
    
    當威脅的狀態被更新時，發布此事件以通知其他模組。
    """
    
    threat_id: str
    old_status: str
    new_status: str
    updated_at: datetime

