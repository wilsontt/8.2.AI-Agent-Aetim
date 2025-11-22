"""
資產管理領域事件

領域事件（Domain Events）用於表示領域中發生的重要事件。
"""

from .asset_created_event import AssetCreatedEvent
from .asset_updated_event import AssetUpdatedEvent

__all__ = [
    "AssetCreatedEvent",
    "AssetUpdatedEvent",
]

