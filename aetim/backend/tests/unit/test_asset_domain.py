"""
資產領域模型單元測試

測試資產聚合根、值物件、實體和領域事件。
"""

import pytest
from datetime import datetime
from asset_management.domain import (
    Asset,
    AssetProduct,
    DataSensitivity,
    BusinessCriticality,
    AssetCreatedEvent,
    AssetUpdatedEvent,
)


@pytest.mark.unit
class TestDataSensitivity:
    """測試資料敏感度值物件"""
    
    def test_create_high_sensitivity(self):
        """測試建立高敏感度"""
        sensitivity = DataSensitivity("高")
        assert sensitivity.value == "高"
        assert sensitivity.weight == 1.5
    
    def test_create_medium_sensitivity(self):
        """測試建立中敏感度"""
        sensitivity = DataSensitivity("中")
        assert sensitivity.value == "中"
        assert sensitivity.weight == 1.0
    
    def test_create_low_sensitivity(self):
        """測試建立低敏感度"""
        sensitivity = DataSensitivity("低")
        assert sensitivity.value == "低"
        assert sensitivity.weight == 0.5
    
    def test_invalid_sensitivity(self):
        """測試無效的敏感度值"""
        with pytest.raises(ValueError, match="資料敏感度必須為"):
            DataSensitivity("無效")
    
    def test_value_equality(self):
        """測試值物件相等性"""
        sensitivity1 = DataSensitivity("高")
        sensitivity2 = DataSensitivity("高")
        assert sensitivity1 == sensitivity2
    
    def test_immutability(self):
        """測試值物件不可變性"""
        sensitivity = DataSensitivity("高")
        with pytest.raises(Exception):  # dataclass frozen 會拋出異常
            sensitivity.value = "中"


@pytest.mark.unit
class TestBusinessCriticality:
    """測試業務關鍵性值物件"""
    
    def test_create_high_criticality(self):
        """測試建立高關鍵性"""
        criticality = BusinessCriticality("高")
        assert criticality.value == "高"
        assert criticality.weight == 1.5
    
    def test_create_medium_criticality(self):
        """測試建立中關鍵性"""
        criticality = BusinessCriticality("中")
        assert criticality.value == "中"
        assert criticality.weight == 1.0
    
    def test_create_low_criticality(self):
        """測試建立低關鍵性"""
        criticality = BusinessCriticality("低")
        assert criticality.value == "低"
        assert criticality.weight == 0.5
    
    def test_invalid_criticality(self):
        """測試無效的關鍵性值"""
        with pytest.raises(ValueError, match="業務關鍵性必須為"):
            BusinessCriticality("無效")
    
    def test_value_equality(self):
        """測試值物件相等性"""
        criticality1 = BusinessCriticality("高")
        criticality2 = BusinessCriticality("高")
        assert criticality1 == criticality2


@pytest.mark.unit
class TestAssetProduct:
    """測試資產產品實體"""
    
    def test_create_product(self):
        """測試建立產品"""
        product = AssetProduct(
            id="test-id",
            product_name="nginx",
            product_version="1.18.0",
        )
        assert product.id == "test-id"
        assert product.product_name == "nginx"
        assert product.product_version == "1.18.0"
    
    def test_create_product_without_id(self):
        """測試建立產品（自動生成 ID）"""
        import uuid
        product = AssetProduct(
            id=str(uuid.uuid4()),
            product_name="nginx",
            product_version="1.18.0",
        )
        assert product.id is not None
        assert len(product.id) > 0
    
    def test_invalid_product_name(self):
        """測試無效的產品名稱"""
        with pytest.raises(ValueError, match="產品名稱不能為空"):
            AssetProduct(id="test-id", product_name="")
    
    def test_entity_equality(self):
        """測試實體相等性（透過 ID）"""
        product1 = AssetProduct(id="same-id", product_name="nginx")
        product2 = AssetProduct(id="same-id", product_name="apache")
        assert product1 == product2  # 相同 ID 即相等


@pytest.mark.unit
class TestAsset:
    """測試資產聚合根"""
    
    def test_create_asset(self):
        """測試建立資產"""
        asset = Asset.create(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="高",
            business_criticality="高",
        )
        
        assert asset.id is not None
        assert asset.host_name == "test-host"
        assert asset.owner == "test-owner"
        assert isinstance(asset.data_sensitivity, DataSensitivity)
        assert isinstance(asset.business_criticality, BusinessCriticality)
        assert asset.data_sensitivity.value == "高"
        assert asset.business_criticality.value == "高"
    
    def test_create_asset_publishes_event(self):
        """測試建立資產發布領域事件"""
        asset = Asset.create(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        
        events = asset.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], AssetCreatedEvent)
        assert events[0].asset_id == asset.id
        assert events[0].host_name == "test-host"
    
    def test_update_asset(self):
        """測試更新資產"""
        asset = Asset.create(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        
        asset.clear_domain_events()
        
        asset.update(
            host_name="updated-host",
            owner="updated-owner",
            updated_by="user1",
        )
        
        assert asset.host_name == "updated-host"
        assert asset.owner == "updated-owner"
        assert asset.updated_by == "user1"
    
    def test_update_asset_publishes_event(self):
        """測試更新資產發布領域事件"""
        asset = Asset.create(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        
        asset.clear_domain_events()
        
        asset.update(host_name="updated-host")
        
        events = asset.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], AssetUpdatedEvent)
        assert events[0].asset_id == asset.id
        assert "host_name" in events[0].updated_fields
    
    def test_add_product(self):
        """測試新增產品資訊"""
        asset = Asset.create(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        
        product = asset.add_product("nginx", "1.18.0")
        
        assert len(asset.products) == 1
        assert product.product_name == "nginx"
        assert product.product_version == "1.18.0"
        assert product in asset.products
    
    def test_add_duplicate_product(self):
        """測試新增重複產品（應拋出異常）"""
        asset = Asset.create(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        
        asset.add_product("nginx", "1.18.0")
        
        with pytest.raises(ValueError, match="產品.*已存在"):
            asset.add_product("nginx", "1.18.0")
    
    def test_remove_product(self):
        """測試移除產品資訊"""
        asset = Asset.create(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        
        product = asset.add_product("nginx", "1.18.0")
        asset.remove_product(product.id)
        
        assert len(asset.products) == 0
    
    def test_remove_nonexistent_product(self):
        """測試移除不存在的產品（應拋出異常）"""
        asset = Asset.create(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        
        with pytest.raises(ValueError, match="產品 ID.*不存在"):
            asset.remove_product("nonexistent-id")
    
    def test_calculate_risk_weight(self):
        """測試計算風險權重"""
        # 高敏感度 × 高關鍵性 = 1.5 × 1.5 = 2.25
        asset = Asset.create(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="高",
            business_criticality="高",
        )
        
        assert asset.calculate_risk_weight() == 2.25
        
        # 中敏感度 × 中關鍵性 = 1.0 × 1.0 = 1.0
        asset.update(data_sensitivity="中", business_criticality="中")
        assert asset.calculate_risk_weight() == 1.0
        
        # 低敏感度 × 低關鍵性 = 0.5 × 0.5 = 0.25
        asset.update(data_sensitivity="低", business_criticality="低")
        assert asset.calculate_risk_weight() == 0.25
    
    def test_invalid_host_name(self):
        """測試無效的主機名稱"""
        with pytest.raises(ValueError, match="主機名稱不能為空"):
            Asset.create(
                host_name="",
                operating_system="Linux 5.4",
                running_applications="nginx 1.18",
                owner="test-owner",
                data_sensitivity="中",
                business_criticality="中",
            )
    
    def test_invalid_owner(self):
        """測試無效的負責人"""
        with pytest.raises(ValueError, match="負責人不能為空"):
            Asset.create(
                host_name="test-host",
                operating_system="Linux 5.4",
                running_applications="nginx 1.18",
                owner="",
                data_sensitivity="中",
                business_criticality="中",
            )
    
    def test_clear_domain_events(self):
        """測試清除領域事件"""
        asset = Asset.create(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        
        assert len(asset.get_domain_events()) == 1
        
        asset.clear_domain_events()
        
        assert len(asset.get_domain_events()) == 0


@pytest.mark.unit
class TestAssetDomainEvents:
    """測試領域事件"""
    
    def test_asset_created_event(self):
        """測試資產建立事件"""
        event = AssetCreatedEvent(
            asset_id="test-id",
            host_name="test-host",
            owner="test-owner",
        )
        
        assert event.asset_id == "test-id"
        assert event.host_name == "test-host"
        assert event.owner == "test-owner"
        assert event.occurred_at is not None
        assert isinstance(event.occurred_at, datetime)
    
    def test_asset_updated_event(self):
        """測試資產更新事件"""
        event = AssetUpdatedEvent(
            asset_id="test-id",
            host_name="test-host",
            updated_fields=["host_name", "owner"],
        )
        
        assert event.asset_id == "test-id"
        assert event.host_name == "test-host"
        assert "host_name" in event.updated_fields
        assert "owner" in event.updated_fields
        assert event.occurred_at is not None

