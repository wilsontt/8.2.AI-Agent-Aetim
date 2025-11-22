"""
資產管理領域介面

定義領域層需要的介面（Repository、外部服務等）。
"""

from .asset_repository import IAssetRepository

__all__ = [
    "IAssetRepository",
]

