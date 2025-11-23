"""
失敗追蹤器單元測試

測試失敗追蹤和告警功能。
"""

import pytest
from datetime import datetime, timedelta
from threat_intelligence.application.services.failure_tracker import (
    FailureTracker,
    FailureRecord,
)


class TestFailureTracker:
    """失敗追蹤器測試"""
    
    def test_record_failure(self):
        """測試記錄失敗"""
        tracker = FailureTracker(failure_threshold=3)
        
        should_alert = tracker.record_failure(
            feed_id="feed-123",
            feed_name="Test Feed",
            error_message="Test error",
            error_type="network_error",
        )
        
        assert should_alert is False  # 第一次失敗，未達閾值
        
        record = tracker.get_failure_record("feed-123")
        assert record is not None
        assert record.failure_count == 1
        assert record.feed_name == "Test Feed"
        assert record.last_error_message == "Test error"
        assert record.last_error_type == "network_error"
    
    def test_record_failure_reaches_threshold(self):
        """測試記錄失敗達到閾值"""
        tracker = FailureTracker(failure_threshold=3)
        
        # 記錄 3 次失敗
        should_alert_1 = tracker.record_failure("feed-123", "Test Feed", "Error 1")
        should_alert_2 = tracker.record_failure("feed-123", "Test Feed", "Error 2")
        should_alert_3 = tracker.record_failure("feed-123", "Test Feed", "Error 3")
        
        assert should_alert_1 is False
        assert should_alert_2 is False
        assert should_alert_3 is True  # 達到閾值，應該發送告警
        
        record = tracker.get_failure_record("feed-123")
        assert record.failure_count == 3
        assert record.alert_sent is True
    
    def test_record_success_resets_failure_count(self):
        """測試記錄成功重置失敗計數"""
        tracker = FailureTracker(failure_threshold=3)
        
        # 記錄 2 次失敗
        tracker.record_failure("feed-123", "Test Feed", "Error 1")
        tracker.record_failure("feed-123", "Test Feed", "Error 2")
        
        record = tracker.get_failure_record("feed-123")
        assert record.failure_count == 2
        
        # 記錄成功
        tracker.record_success("feed-123")
        
        record = tracker.get_failure_record("feed-123")
        assert record.failure_count == 0
        assert record.alert_sent is False
    
    def test_alert_cooldown(self):
        """測試告警冷卻時間"""
        tracker = FailureTracker(failure_threshold=3, alert_cooldown_hours=24)
        
        # 記錄 3 次失敗（達到閾值）
        should_alert_1 = tracker.record_failure("feed-123", "Test Feed", "Error 1")
        should_alert_2 = tracker.record_failure("feed-123", "Test Feed", "Error 2")
        should_alert_3 = tracker.record_failure("feed-123", "Test Feed", "Error 3")
        
        assert should_alert_3 is True  # 第一次達到閾值，應該發送告警
        
        # 繼續記錄失敗（在冷卻時間內）
        should_alert_4 = tracker.record_failure("feed-123", "Test Feed", "Error 4")
        assert should_alert_4 is False  # 在冷卻時間內，不發送告警
    
    def test_multiple_feeds_tracking(self):
        """測試追蹤多個來源"""
        tracker = FailureTracker(failure_threshold=3)
        
        # 記錄不同來源的失敗
        tracker.record_failure("feed-1", "Feed 1", "Error 1")
        tracker.record_failure("feed-2", "Feed 2", "Error 2")
        tracker.record_failure("feed-1", "Feed 1", "Error 3")
        
        record_1 = tracker.get_failure_record("feed-1")
        record_2 = tracker.get_failure_record("feed-2")
        
        assert record_1.failure_count == 2
        assert record_2.failure_count == 1
    
    def test_get_all_failure_records(self):
        """測試取得所有失敗記錄"""
        tracker = FailureTracker(failure_threshold=3)
        
        tracker.record_failure("feed-1", "Feed 1", "Error 1")
        tracker.record_failure("feed-2", "Feed 2", "Error 2")
        
        all_records = tracker.get_all_failure_records()
        
        assert len(all_records) == 2
        assert "feed-1" in all_records
        assert "feed-2" in all_records

