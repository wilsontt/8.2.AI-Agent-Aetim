"""
威脅領域模型單元測試

測試威脅領域模型的所有業務邏輯和規則。
"""

import pytest
from datetime import datetime
import sys
import os

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.value_objects.threat_severity import ThreatSeverity
from threat_intelligence.domain.value_objects.threat_status import ThreatStatus
from threat_intelligence.domain.entities.threat_product import ThreatProduct
from threat_intelligence.domain.domain_events.threat_created_event import ThreatCreatedEvent
from threat_intelligence.domain.domain_events.threat_status_updated_event import ThreatStatusUpdatedEvent
from threat_intelligence.domain.domain_events.threat_updated_event import ThreatUpdatedEvent


class TestThreatSeverity:
    """測試 ThreatSeverity 值物件"""
    
    def test_create_valid_severity(self):
        """測試建立有效的嚴重程度"""
        severity = ThreatSeverity("Critical")
        assert severity.value == "Critical"
        assert severity.weight == 1.5
    
    def test_create_invalid_severity(self):
        """測試建立無效的嚴重程度"""
        with pytest.raises(ValueError, match="嚴重程度必須為"):
            ThreatSeverity("Invalid")
    
    def test_severity_weights(self):
        """測試嚴重程度權重"""
        assert ThreatSeverity("Critical").weight == 1.5
        assert ThreatSeverity("High").weight == 1.2
        assert ThreatSeverity("Medium").weight == 1.0
        assert ThreatSeverity("Low").weight == 0.8


class TestThreatStatus:
    """測試 ThreatStatus 值物件"""
    
    def test_create_valid_status(self):
        """測試建立有效的狀態"""
        status = ThreatStatus("New")
        assert status.value == "New"
    
    def test_create_invalid_status(self):
        """測試建立無效的狀態"""
        with pytest.raises(ValueError, match="狀態必須為"):
            ThreatStatus("Invalid")
    
    def test_status_transitions(self):
        """測試狀態轉換規則"""
        new_status = ThreatStatus("New")
        assert new_status.can_transition_to("Analyzing") is True
        assert new_status.can_transition_to("Closed") is True
        assert new_status.can_transition_to("Processed") is False
        
        analyzing_status = ThreatStatus("Analyzing")
        assert analyzing_status.can_transition_to("Processed") is True
        assert analyzing_status.can_transition_to("Closed") is True
        assert analyzing_status.can_transition_to("New") is False
        
        processed_status = ThreatStatus("Processed")
        assert processed_status.can_transition_to("Closed") is True
        assert processed_status.can_transition_to("New") is False
        
        closed_status = ThreatStatus("Closed")
        assert closed_status.can_transition_to("New") is False
        assert closed_status.can_transition_to("Analyzing") is False


class TestThreatProduct:
    """測試 ThreatProduct 實體"""
    
    def test_create_product(self):
        """測試建立產品"""
        product = ThreatProduct(
            id="test-id",
            product_name="VMware ESXi",
            product_version="7.0.3",
        )
        assert product.product_name == "VMware ESXi"
        assert product.product_version == "7.0.3"
    
    def test_create_product_without_version(self):
        """測試建立沒有版本的產品"""
        product = ThreatProduct(
            id="test-id",
            product_name="Windows Server",
        )
        assert product.product_version is None
    
    def test_create_product_with_empty_name(self):
        """測試建立空名稱的產品"""
        with pytest.raises(ValueError, match="產品名稱不能為空"):
            ThreatProduct(id="test-id", product_name="")


class TestThreat:
    """測試 Threat 聚合根"""
    
    def test_create_threat(self):
        """測試建立威脅"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
            description="Test Description",
            cve_id="CVE-2024-12345",
            cvss_base_score=9.8,
        )
        
        assert threat.id is not None
        assert threat.threat_feed_id == "feed-1"
        assert threat.title == "Test Threat"
        assert threat.cve_id == "CVE-2024-12345"
        assert threat.cvss_base_score == 9.8
        assert threat.status.value == "New"
        
        # 檢查領域事件
        events = threat.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], ThreatCreatedEvent)
        assert events[0].threat_id == threat.id
    
    def test_create_threat_with_severity(self):
        """測試建立帶有嚴重程度的威脅"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
            severity=ThreatSeverity("High"),
        )
        
        assert threat.severity.value == "High"
    
    def test_create_threat_auto_determine_severity(self):
        """測試根據 CVSS 分數自動決定嚴重程度"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
            cvss_base_score=9.8,
        )
        
        assert threat.severity.value == "Critical"
        
        threat2 = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat 2",
            cvss_base_score=7.5,
        )
        
        assert threat2.severity.value == "High"
        
        threat3 = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat 3",
            cvss_base_score=5.0,
        )
        
        assert threat3.severity.value == "Medium"
        
        threat4 = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat 4",
            cvss_base_score=2.0,
        )
        
        assert threat4.severity.value == "Low"
    
    def test_create_threat_with_empty_title(self):
        """測試建立空標題的威脅"""
        with pytest.raises(ValueError, match="威脅標題不能為空"):
            Threat.create(
                threat_feed_id="feed-1",
                title="",
            )
    
    def test_update_status(self):
        """測試更新狀態"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        threat.update_status("Analyzing")
        assert threat.status.value == "Analyzing"
        
        events = threat.get_domain_events()
        assert len(events) == 2  # Created + StatusUpdated
        assert isinstance(events[1], ThreatStatusUpdatedEvent)
        assert events[1].old_status == "New"
        assert events[1].new_status == "Analyzing"
    
    def test_update_status_invalid_transition(self):
        """測試無效的狀態轉換"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        with pytest.raises(ValueError, match="無法從狀態"):
            threat.update_status("Processed")  # New 不能直接轉換到 Processed
    
    def test_add_product(self):
        """測試新增產品"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        threat.add_product("VMware ESXi", "7.0.3")
        assert len(threat.products) == 1
        assert threat.products[0].product_name == "VMware ESXi"
        assert threat.products[0].product_version == "7.0.3"
        
        events = threat.get_domain_events()
        assert len(events) == 2  # Created + Updated
        assert isinstance(events[1], ThreatUpdatedEvent)
        assert "products" in events[1].updated_fields
    
    def test_add_duplicate_product(self):
        """測試新增重複的產品"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        threat.add_product("VMware ESXi", "7.0.3")
        threat.add_product("VMware ESXi", "7.0.3")  # 重複
        
        assert len(threat.products) == 1  # 不應重複新增
    
    def test_add_ttp(self):
        """測試新增 TTP"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        threat.add_ttp("T1566.001")
        assert "T1566.001" in threat.ttps
        
        events = threat.get_domain_events()
        assert len(events) == 2  # Created + Updated
        assert isinstance(events[1], ThreatUpdatedEvent)
        assert "ttps" in events[1].updated_fields
    
    def test_add_duplicate_ttp(self):
        """測試新增重複的 TTP"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        threat.add_ttp("T1566.001")
        threat.add_ttp("T1566.001")  # 重複
        
        assert threat.ttps.count("T1566.001") == 1  # 不應重複新增
    
    def test_add_ioc(self):
        """測試新增 IOC"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        threat.add_ioc("ips", "192.168.1.1")
        assert "192.168.1.1" in threat.iocs["ips"]
        
        threat.add_ioc("domains", "malicious.com")
        assert "malicious.com" in threat.iocs["domains"]
        
        events = threat.get_domain_events()
        assert len(events) == 3  # Created + Updated (ips) + Updated (domains)
    
    def test_add_duplicate_ioc(self):
        """測試新增重複的 IOC"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        threat.add_ioc("ips", "192.168.1.1")
        threat.add_ioc("ips", "192.168.1.1")  # 重複
        
        assert threat.iocs["ips"].count("192.168.1.1") == 1  # 不應重複新增
    
    def test_update_threat(self):
        """測試更新威脅"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        threat.update(
            title="Updated Title",
            description="Updated Description",
            cvss_base_score=8.5,
        )
        
        assert threat.title == "Updated Title"
        assert threat.description == "Updated Description"
        assert threat.cvss_base_score == 8.5
        
        events = threat.get_domain_events()
        assert len(events) == 2  # Created + Updated
        assert isinstance(events[1], ThreatUpdatedEvent)
        assert "title" in events[1].updated_fields
        assert "description" in events[1].updated_fields
        assert "cvss_base_score" in events[1].updated_fields
    
    def test_update_threat_with_empty_title(self):
        """測試更新為空標題"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        with pytest.raises(ValueError, match="威脅標題不能為空"):
            threat.update(title="")
    
    def test_clear_domain_events(self):
        """測試清除領域事件"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        assert len(threat.get_domain_events()) > 0
        
        threat.clear_domain_events()
        assert len(threat.get_domain_events()) == 0
    
    def test_status_lifecycle(self):
        """測試完整的狀態生命週期"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
        )
        
        assert threat.status.value == "New"
        
        threat.update_status("Analyzing")
        assert threat.status.value == "Analyzing"
        
        threat.update_status("Processed")
        assert threat.status.value == "Processed"
        
        threat.update_status("Closed")
        assert threat.status.value == "Closed"
        
        # 已關閉的狀態不能再轉換
        with pytest.raises(ValueError, match="無法從狀態"):
            threat.update_status("Analyzing")

