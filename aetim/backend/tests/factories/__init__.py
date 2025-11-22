"""
測試資料工廠

使用 Factory Pattern 建立測試資料。
"""

from .asset_factory import AssetFactory, AssetProductFactory
from .threat_factory import ThreatFeedFactory, ThreatFactory
from .pir_factory import PIRFactory
from .user_factory import UserFactory, RoleFactory, PermissionFactory

__all__ = [
    "AssetFactory",
    "AssetProductFactory",
    "ThreatFeedFactory",
    "ThreatFactory",
    "PIRFactory",
    "UserFactory",
    "RoleFactory",
    "PermissionFactory",
]

