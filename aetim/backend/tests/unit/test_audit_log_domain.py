"""
稽核日誌領域模型單元測試

測試 AuditLog 實體的建立、驗證和業務邏輯。
"""

import pytest
from datetime import datetime
from system_management.domain.entities.audit_log import AuditLog


class TestAuditLog:
    """稽核日誌實體測試"""
    
    def test_create_audit_log_success(self):
        """測試成功建立稽核日誌"""
        audit_log = AuditLog.create(
            user_id="user-123",
            action="CREATE",
            resource_type="Asset",
            resource_id="asset-456",
            details={"field": "value"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        
        assert audit_log.id is not None
        assert audit_log.user_id == "user-123"
        assert audit_log.action == "CREATE"
        assert audit_log.resource_type == "Asset"
        assert audit_log.resource_id == "asset-456"
        assert audit_log.details == {"field": "value"}
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.user_agent == "Mozilla/5.0"
        assert isinstance(audit_log.created_at, datetime)
    
    def test_create_audit_log_without_optional_fields(self):
        """測試建立稽核日誌（不包含可選欄位）"""
        audit_log = AuditLog.create(
            user_id=None,
            action="VIEW",
            resource_type="Asset",
        )
        
        assert audit_log.id is not None
        assert audit_log.user_id is None
        assert audit_log.action == "VIEW"
        assert audit_log.resource_type == "Asset"
        assert audit_log.resource_id is None
        assert audit_log.details is None
        assert audit_log.ip_address is None
        assert audit_log.user_agent is None
    
    def test_create_audit_log_action_uppercase(self):
        """測試操作類型自動轉為大寫"""
        audit_log = AuditLog.create(
            user_id="user-123",
            action="create",
            resource_type="Asset",
        )
        
        assert audit_log.action == "CREATE"
    
    def test_create_audit_log_invalid_action_empty(self):
        """測試建立稽核日誌（操作類型為空）"""
        with pytest.raises(ValueError, match="操作類型不能為空"):
            AuditLog.create(
                user_id="user-123",
                action="",
                resource_type="Asset",
            )
    
    def test_create_audit_log_invalid_action_whitespace(self):
        """測試建立稽核日誌（操作類型為空白）"""
        with pytest.raises(ValueError, match="操作類型不能為空"):
            AuditLog.create(
                user_id="user-123",
                action="   ",
                resource_type="Asset",
            )
    
    def test_create_audit_log_invalid_action_invalid_value(self):
        """測試建立稽核日誌（無效的操作類型）"""
        with pytest.raises(ValueError, match="操作類型必須為以下之一"):
            AuditLog.create(
                user_id="user-123",
                action="INVALID",
                resource_type="Asset",
            )
    
    def test_create_audit_log_invalid_resource_type_empty(self):
        """測試建立稽核日誌（資源類型為空）"""
        with pytest.raises(ValueError, match="資源類型不能為空"):
            AuditLog.create(
                user_id="user-123",
                action="CREATE",
                resource_type="",
            )
    
    def test_create_audit_log_valid_actions(self):
        """測試所有有效的操作類型"""
        valid_actions = ["CREATE", "UPDATE", "DELETE", "IMPORT", "VIEW", "TOGGLE", "EXPORT"]
        
        for action in valid_actions:
            audit_log = AuditLog.create(
                user_id="user-123",
                action=action,
                resource_type="Asset",
            )
            assert audit_log.action == action
    
    def test_to_dict(self):
        """測試轉換為字典格式"""
        audit_log = AuditLog.create(
            user_id="user-123",
            action="CREATE",
            resource_type="Asset",
            resource_id="asset-456",
            details={"field": "value"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        
        audit_dict = audit_log.to_dict()
        
        assert audit_dict["id"] == audit_log.id
        assert audit_dict["user_id"] == "user-123"
        assert audit_dict["action"] == "CREATE"
        assert audit_dict["resource_type"] == "Asset"
        assert audit_dict["resource_id"] == "asset-456"
        assert audit_dict["ip_address"] == "192.168.1.1"
        assert audit_dict["user_agent"] == "Mozilla/5.0"
        assert isinstance(audit_dict["created_at"], datetime)
        # details 應該被轉換為 JSON 字串
        assert isinstance(audit_dict["details"], str)
    
    def test_to_dict_with_none_details(self):
        """測試轉換為字典格式（details 為 None）"""
        audit_log = AuditLog.create(
            user_id="user-123",
            action="VIEW",
            resource_type="Asset",
        )
        
        audit_dict = audit_log.to_dict()
        
        assert audit_dict["details"] is None
    
    def test_repr(self):
        """測試字串表示"""
        audit_log = AuditLog.create(
            user_id="user-123",
            action="CREATE",
            resource_type="Asset",
            resource_id="asset-456",
        )
        
        repr_str = repr(audit_log)
        
        assert "AuditLog" in repr_str
        assert audit_log.id in repr_str
        assert "CREATE" in repr_str
        assert "Asset" in repr_str
        assert "asset-456" in repr_str

