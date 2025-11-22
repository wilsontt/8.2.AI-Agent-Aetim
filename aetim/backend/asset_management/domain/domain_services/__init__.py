"""
資產管理領域服務

領域服務（Domain Services）包含不屬於單一聚合的業務邏輯。
"""

from .asset_parsing_service import AssetParsingService

__all__ = [
    "AssetParsingService",
]

