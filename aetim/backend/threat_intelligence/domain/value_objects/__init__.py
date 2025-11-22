"""
威脅情資領域值物件

值物件（Value Objects）是不可變的，沒有唯一識別碼，透過值相等性比較。
"""

from .threat_feed_priority import ThreatFeedPriority
from .collection_frequency import CollectionFrequency
from .collection_status import CollectionStatus

__all__ = [
    "ThreatFeedPriority",
    "CollectionFrequency",
    "CollectionStatus",
]

