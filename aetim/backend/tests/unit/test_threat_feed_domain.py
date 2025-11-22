"""
威脅情資來源領域模型單元測試

測試 ThreatFeed 聚合根、值物件和領域事件的邏輯。
"""

import pytest
from datetime import datetime
from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed
from threat_intelligence.domain.value_objects.threat_feed_priority import ThreatFeedPriority
from threat_intelligence.domain.value_objects.collection_frequency import CollectionFrequency
from threat_intelligence.domain.value_objects.collection_status import CollectionStatus
from threat_intelligence.domain.domain_events.threat_feed_created_event import ThreatFeedCreatedEvent
from threat_intelligence.domain.domain_events.threat_feed_updated_event import ThreatFeedUpdatedEvent
from threat_intelligence.domain.domain_events.collection_status_updated_event import CollectionStatusUpdatedEvent


class TestThreatFeedPriority:
    """測試 ThreatFeedPriority 值物件"""
    
    def test_create_valid_priority(self):
        """測試建立有效的優先級"""
        priority = ThreatFeedPriority("P0")
        assert priority.value == "P0"
        assert priority.numeric_value == 0
    
    def test_create_invalid_priority(self):
        """測試建立無效的優先級"""
        with pytest.raises(ValueError, match="威脅情資來源優先級必須為"):
            ThreatFeedPriority("P4")
    
    def test_priority_equality(self):
        """測試優先級相等性"""
        priority1 = ThreatFeedPriority("P0")
        priority2 = ThreatFeedPriority("P0")
        assert priority1 == priority2


class TestCollectionFrequency:
    """測試 CollectionFrequency 值物件"""
    
    def test_create_valid_frequency(self):
        """測試建立有效的收集頻率"""
        frequency = CollectionFrequency("每小時")
        assert frequency.value == "每小時"
        assert frequency.hours == 1
    
    def test_create_invalid_frequency(self):
        """測試建立無效的收集頻率"""
        with pytest.raises(ValueError, match="收集頻率必須為以下之一"):
            CollectionFrequency("每秒")


class TestCollectionStatus:
    """測試 CollectionStatus 值物件"""
    
    def test_create_valid_status(self):
        """測試建立有效的收集狀態"""
        status = CollectionStatus("success")
        assert status.value == "success"
        assert status.is_success is True
        assert status.is_failed is False
        assert status.is_in_progress is False


class TestThreatFeed:
    """測試 ThreatFeed 聚合根"""
    
    def test_create_threat_feed(self):
        """測試建立威脅情資來源"""
        threat_feed = ThreatFeed.create(
            name="CISA KEV",
            priority="P0",
            collection_frequency="每小時",
        )
        
        assert threat_feed.id is not None
        assert threat_feed.name == "CISA KEV"
        assert threat_feed.priority.value == "P0"
        assert threat_feed.collection_frequency.value == "每小時"
        assert threat_feed.is_enabled is True
        
        # 檢查領域事件
        events = threat_feed.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], ThreatFeedCreatedEvent)
        assert events[0].threat_feed_id == threat_feed.id
    
    def test_create_threat_feed_with_empty_name(self):
        """測試建立威脅情資來源時名稱為空"""
        with pytest.raises(ValueError, match="威脅情資來源名稱不能為空"):
            ThreatFeed.create(
                name="",
                priority="P0",
                collection_frequency="每小時",
            )
    
    def test_update_threat_feed(self):
        """測試更新威脅情資來源"""
        threat_feed = ThreatFeed.create(
            name="CISA KEV",
            priority="P0",
            collection_frequency="每小時",
        )
        
        threat_feed.clear_domain_events()
        
        threat_feed.update(
            name="NVD",
            priority="P1",
            updated_by="user1",
        )
        
        assert threat_feed.name == "NVD"
        assert threat_feed.priority.value == "P1"
        assert threat_feed.updated_by == "user1"
        
        # 檢查領域事件
        events = threat_feed.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], ThreatFeedUpdatedEvent)
        assert "name" in events[0].updated_fields
        assert "priority" in events[0].updated_fields
    
    def test_toggle_threat_feed(self):
        """測試切換威脅情資來源啟用狀態"""
        threat_feed = ThreatFeed.create(
            name="CISA KEV",
            priority="P0",
            collection_frequency="每小時",
        )
        
        assert threat_feed.is_enabled is True
        
        threat_feed.clear_domain_events()
        
        threat_feed.toggle(updated_by="user1")
        
        assert threat_feed.is_enabled is False
        assert threat_feed.updated_by == "user1"
    
    def test_update_collection_status(self):
        """測試更新收集狀態"""
        threat_feed = ThreatFeed.create(
            name="CISA KEV",
            priority="P0",
            collection_frequency="每小時",
        )
        
        threat_feed.clear_domain_events()
        
        threat_feed.update_collection_status("success", record_count=10)
        
        assert threat_feed.last_collection_status.value == "success"
        assert threat_feed.last_collection_time is not None
        
        # 檢查領域事件
        events = threat_feed.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], CollectionStatusUpdatedEvent)
        assert events[0].status == "success"
        assert events[0].record_count == 10
    
    def test_update_collection_status_with_error(self):
        """測試更新收集狀態（失敗）"""
        threat_feed = ThreatFeed.create(
            name="CISA KEV",
            priority="P0",
            collection_frequency="每小時",
        )
        
        threat_feed.update_collection_status("failed", error_message="連線失敗")
        
        assert threat_feed.last_collection_status.value == "failed"
        assert threat_feed.last_collection_error == "連線失敗"

