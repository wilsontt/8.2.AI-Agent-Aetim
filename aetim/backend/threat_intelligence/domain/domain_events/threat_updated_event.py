"""
威脅更新事件

當威脅的其他屬性被更新時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass(frozen=True)
class ThreatUpdatedEvent:
    """
    威脅更新事件
    
    當威脅的屬性（非狀態）被更新時，發布此事件以通知其他模組。
    """
    
    threat_id: str
    updated_fields: List[str]  # 被更新的欄位列表
    updated_at: datetime

