"""
PIR 領域模型單元測試

測試 PIR 聚合根、值物件和領域事件的邏輯。
"""

import pytest
from datetime import datetime
from analysis_assessment.domain.aggregates.pir import PIR
from analysis_assessment.domain.value_objects.pir_priority import PIRPriority
from analysis_assessment.domain.domain_events.pir_created_event import PIRCreatedEvent
from analysis_assessment.domain.domain_events.pir_updated_event import PIRUpdatedEvent
from analysis_assessment.domain.domain_events.pir_toggled_event import PIRToggledEvent


class TestPIRPriority:
    """測試 PIRPriority 值物件"""
    
    def test_create_valid_priority(self):
        """測試建立有效的優先級"""
        priority = PIRPriority("高")
        assert priority.value == "高"
    
    def test_create_invalid_priority(self):
        """測試建立無效的優先級"""
        with pytest.raises(ValueError, match="PIR 優先級必須為"):
            PIRPriority("無效")
    
    def test_priority_equality(self):
        """測試優先級相等性"""
        priority1 = PIRPriority("高")
        priority2 = PIRPriority("高")
        assert priority1 == priority2
    
    def test_priority_hash(self):
        """測試優先級可雜湊"""
        priority = PIRPriority("高")
        assert hash(priority) == hash(PIRPriority("高"))


class TestPIR:
    """測試 PIR 聚合根"""
    
    def test_create_pir(self):
        """測試建立 PIR"""
        pir = PIR.create(
            name="測試 PIR",
            description="測試描述",
            priority="高",
            condition_type="產品名稱",
            condition_value="VMware",
        )
        
        assert pir.id is not None
        assert pir.name == "測試 PIR"
        assert pir.description == "測試描述"
        assert pir.priority.value == "高"
        assert pir.condition_type == "產品名稱"
        assert pir.condition_value == "VMware"
        assert pir.is_enabled is True
        
        # 檢查領域事件
        events = pir.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], PIRCreatedEvent)
        assert events[0].pir_id == pir.id
    
    def test_create_pir_with_empty_name(self):
        """測試建立 PIR 時名稱為空"""
        with pytest.raises(ValueError, match="PIR 名稱不能為空"):
            PIR.create(
                name="",
                description="測試描述",
                priority="高",
                condition_type="產品名稱",
                condition_value="VMware",
            )
    
    def test_create_pir_with_empty_description(self):
        """測試建立 PIR 時描述為空"""
        with pytest.raises(ValueError, match="PIR 描述不能為空"):
            PIR.create(
                name="測試 PIR",
                description="",
                priority="高",
                condition_type="產品名稱",
                condition_value="VMware",
            )
    
    def test_update_pir(self):
        """測試更新 PIR"""
        pir = PIR.create(
            name="測試 PIR",
            description="測試描述",
            priority="高",
            condition_type="產品名稱",
            condition_value="VMware",
        )
        
        pir.clear_domain_events()
        
        pir.update(
            name="更新後的 PIR",
            description="更新後的描述",
            updated_by="user1",
        )
        
        assert pir.name == "更新後的 PIR"
        assert pir.description == "更新後的描述"
        assert pir.updated_by == "user1"
        
        # 檢查領域事件
        events = pir.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], PIRUpdatedEvent)
        assert "name" in events[0].updated_fields
        assert "description" in events[0].updated_fields
    
    def test_toggle_pir(self):
        """測試切換 PIR 啟用狀態"""
        pir = PIR.create(
            name="測試 PIR",
            description="測試描述",
            priority="高",
            condition_type="產品名稱",
            condition_value="VMware",
        )
        
        assert pir.is_enabled is True
        
        pir.clear_domain_events()
        
        pir.toggle(updated_by="user1")
        
        assert pir.is_enabled is False
        assert pir.updated_by == "user1"
        
        # 檢查領域事件
        events = pir.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], PIRToggledEvent)
        assert events[0].is_enabled is False
    
    def test_enable_pir(self):
        """測試啟用 PIR"""
        pir = PIR.create(
            name="測試 PIR",
            description="測試描述",
            priority="高",
            condition_type="產品名稱",
            condition_value="VMware",
            is_enabled=False,
        )
        
        assert pir.is_enabled is False
        
        pir.enable()
        
        assert pir.is_enabled is True
    
    def test_disable_pir(self):
        """測試停用 PIR"""
        pir = PIR.create(
            name="測試 PIR",
            description="測試描述",
            priority="高",
            condition_type="產品名稱",
            condition_value="VMware",
            is_enabled=True,
        )
        
        assert pir.is_enabled is True
        
        pir.disable()
        
        assert pir.is_enabled is False
    
    def test_matches_condition_product_name(self):
        """測試產品名稱條件匹配"""
        pir = PIR.create(
            name="VMware PIR",
            description="VMware 相關威脅",
            priority="高",
            condition_type="產品名稱",
            condition_value="VMware",
        )
        
        # 匹配
        assert pir.matches_condition({"product_name": "VMware ESXi"}) is True
        assert pir.matches_condition({"product_name": "vmware vcenter"}) is True
        
        # 不匹配
        assert pir.matches_condition({"product_name": "Microsoft SQL Server"}) is False
    
    def test_matches_condition_cve(self):
        """測試 CVE 編號條件匹配"""
        pir = PIR.create(
            name="CVE-2024 PIR",
            description="2024 年 CVE",
            priority="高",
            condition_type="CVE 編號",
            condition_value="CVE-2024-",
        )
        
        # 匹配（前綴匹配）
        assert pir.matches_condition({"cve": "CVE-2024-1234"}) is True
        
        # 不匹配
        assert pir.matches_condition({"cve": "CVE-2023-5678"}) is False
    
    def test_matches_condition_disabled_pir(self):
        """測試停用的 PIR 不匹配條件（業務規則 AC-005-2）"""
        pir = PIR.create(
            name="測試 PIR",
            description="測試描述",
            priority="高",
            condition_type="產品名稱",
            condition_value="VMware",
            is_enabled=False,
        )
        
        # 停用的 PIR 不應匹配任何條件
        assert pir.matches_condition({"product_name": "VMware ESXi"}) is False
    
    def test_clear_domain_events(self):
        """測試清除領域事件"""
        pir = PIR.create(
            name="測試 PIR",
            description="測試描述",
            priority="高",
            condition_type="產品名稱",
            condition_value="VMware",
        )
        
        assert len(pir.get_domain_events()) == 1
        
        pir.clear_domain_events()
        
        assert len(pir.get_domain_events()) == 0

