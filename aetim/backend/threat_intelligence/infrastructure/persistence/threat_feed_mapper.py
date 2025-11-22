"""
威脅情資來源領域模型與資料模型映射器

負責領域模型（ThreatFeed）與資料模型（ThreatFeed）之間的轉換。
"""

from ...domain.aggregates.threat_feed import ThreatFeed
from ...domain.value_objects.threat_feed_priority import ThreatFeedPriority
from ...domain.value_objects.collection_frequency import CollectionFrequency
from ...domain.value_objects.collection_status import CollectionStatus
from .models import ThreatFeed as ThreatFeedModel


class ThreatFeedMapper:
    """威脅情資來源映射器"""
    
    @staticmethod
    def to_domain(threat_feed_model: ThreatFeedModel) -> ThreatFeed:
        """
        將資料模型轉換為領域模型
        
        Args:
            threat_feed_model: 資料模型
        
        Returns:
            ThreatFeed: 領域模型（聚合根）
        """
        threat_feed = ThreatFeed(
            id=str(threat_feed_model.id),
            name=threat_feed_model.name,
            description=threat_feed_model.description,
            priority=ThreatFeedPriority(threat_feed_model.priority),
            is_enabled=threat_feed_model.is_enabled,
            collection_frequency=CollectionFrequency(threat_feed_model.collection_frequency) if threat_feed_model.collection_frequency else None,
            collection_strategy=threat_feed_model.collection_strategy,
            api_key=threat_feed_model.api_key,
            last_collection_time=threat_feed_model.last_collection_time,
            last_collection_status=CollectionStatus(threat_feed_model.last_collection_status) if threat_feed_model.last_collection_status else None,
            last_collection_error=threat_feed_model.last_collection_error,
            created_at=threat_feed_model.created_at,
            updated_at=threat_feed_model.updated_at,
            created_by=threat_feed_model.created_by,
            updated_by=threat_feed_model.updated_by,
        )
        
        # 清除領域事件（從資料庫載入的物件不應有未發布的事件）
        threat_feed.clear_domain_events()
        
        return threat_feed
    
    @staticmethod
    def to_model(threat_feed: ThreatFeed) -> ThreatFeedModel:
        """
        將領域模型轉換為資料模型
        
        Args:
            threat_feed: 領域模型（聚合根）
        
        Returns:
            ThreatFeedModel: 資料模型
        """
        return ThreatFeedModel(
            id=threat_feed.id,
            name=threat_feed.name,
            description=threat_feed.description,
            priority=threat_feed.priority.value,
            is_enabled=threat_feed.is_enabled,
            collection_frequency=threat_feed.collection_frequency.value if threat_feed.collection_frequency else None,
            collection_strategy=threat_feed.collection_strategy,
            api_key=threat_feed.api_key,
            last_collection_time=threat_feed.last_collection_time,
            last_collection_status=threat_feed.last_collection_status.value if threat_feed.last_collection_status else None,
            last_collection_error=threat_feed.last_collection_error,
            created_at=threat_feed.created_at,
            updated_at=threat_feed.updated_at,
            created_by=threat_feed.created_by,
            updated_by=threat_feed.updated_by,
        )
    
    @staticmethod
    def update_model(threat_feed_model: ThreatFeedModel, threat_feed: ThreatFeed) -> None:
        """
        更新資料模型（不建立新物件）
        
        Args:
            threat_feed_model: 現有的資料模型
            threat_feed: 領域模型（聚合根）
        """
        threat_feed_model.name = threat_feed.name
        threat_feed_model.description = threat_feed.description
        threat_feed_model.priority = threat_feed.priority.value
        threat_feed_model.is_enabled = threat_feed.is_enabled
        threat_feed_model.collection_frequency = threat_feed.collection_frequency.value if threat_feed.collection_frequency else None
        threat_feed_model.collection_strategy = threat_feed.collection_strategy
        threat_feed_model.api_key = threat_feed.api_key
        threat_feed_model.last_collection_time = threat_feed.last_collection_time
        threat_feed_model.last_collection_status = threat_feed.last_collection_status.value if threat_feed.last_collection_status else None
        threat_feed_model.last_collection_error = threat_feed.last_collection_error
        threat_feed_model.updated_at = threat_feed.updated_at
        threat_feed_model.updated_by = threat_feed.updated_by

