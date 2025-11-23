"""
威脅情資持久化層

實作 Repository 和資料模型映射。
"""

from .threat_feed_repository import ThreatFeedRepository
from .threat_feed_mapper import ThreatFeedMapper
from .threat_repository import ThreatRepository
from .threat_mapper import ThreatMapper
from .threat_asset_association_repository import ThreatAssetAssociationRepository

__all__ = [
    "ThreatFeedRepository",
    "ThreatFeedMapper",
    "ThreatRepository",
    "ThreatMapper",
    "ThreatAssetAssociationRepository",
]

# 為了方便匯入，也提供直接匯出
ThreatRepository = ThreatRepository
ThreatMapper = ThreatMapper
ThreatAssetAssociationRepository = ThreatAssetAssociationRepository

