"""
資產管理持久化層

實作 Repository 和資料模型映射。
"""

from .asset_repository import AssetRepository
from .asset_mapper import AssetMapper

__all__ = [
    "AssetRepository",
    "AssetMapper",
]

