"""
威脅建立事件

當威脅被建立時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ThreatCreatedEvent:
    """
    威脅建立事件
    
    當新的威脅被建立時，發布此事件以通知其他模組。
    """
    
    threat_id: str
    cve_id: str | None
    threat_feed_id: str
    created_at: datetime

