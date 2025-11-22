"""
資產管理領域聚合根

聚合根（Aggregate Root）是聚合的入口點，負責維護聚合的一致性邊界。
"""

from .asset import Asset

__all__ = [
    "Asset",
]

