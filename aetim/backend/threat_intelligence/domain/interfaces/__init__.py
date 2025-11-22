"""
威脅情資領域介面

定義領域層需要的介面（Repository、外部服務等）。
"""

from .threat_feed_repository import IThreatFeedRepository

__all__ = [
    "IThreatFeedRepository",
]

