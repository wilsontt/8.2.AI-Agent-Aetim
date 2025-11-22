"""
資產管理領域層

領域層包含：
- 聚合根（Aggregates）
- 實體（Entities）
- 值物件（Value Objects）
- 領域事件（Domain Events）
- 領域服務（Domain Services）
- 介面（Interfaces）
"""

from .aggregates.asset import Asset
from .entities.asset_product import AssetProduct
from .value_objects.data_sensitivity import DataSensitivity
from .value_objects.business_criticality import BusinessCriticality
from .domain_events.asset_created_event import AssetCreatedEvent
from .domain_events.asset_updated_event import AssetUpdatedEvent

__all__ = [
    "Asset",
    "AssetProduct",
    "DataSensitivity",
    "BusinessCriticality",
    "AssetCreatedEvent",
    "AssetUpdatedEvent",
]

